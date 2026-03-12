import math
import torch
import torch.nn as nn
import torch.utils.data
import torchvision.models as models
import torch.nn.init as init

class SMARTModel(nn.Module):
    def __init__(self, vocab_size=2 ** 8, n_embd=180, n_fp=2048):
        super().__init__()
        self.vocab_size = vocab_size

        # A trick to map image to RGB space
        self.proj = nn.Conv2d(1, 3, 1)
        self.features = models.squeezenet1_1(weights=models.SqueezeNet1_1_Weights.DEFAULT).features

        self.final_proj = nn.Sequential(
            nn.Dropout(0.5),
            nn.Conv2d(512, n_embd // 36, kernel_size=1),
        )

        self.fp_classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(n_embd, n_fp)
        )

        self.dropout = nn.Dropout(0.2)

        # TODO: Customize attention mask
        self.transformer = GPT2Model(GPT2Config(
            vocab_size=vocab_size,
            n_positions=512,
            n_embd=n_embd,
            n_ff=n_embd * 4,
            n_layer=6,
            n_head=4
        ))

        # Character embedding
        self.embed = nn.Embedding(vocab_size, n_embd)        
        # Tied decoder weights
        embeddings = self.embed
        embed_shape = embeddings.weight.shape
        self.decoder = nn.Linear(embed_shape[1], embed_shape[0], bias=False)
        self.decoder.weight = embeddings.weight
        embeddings.weight.data.normal_(mean=0.0, std=0.02)

    def compute_image(self, image):
        # Process image
        image = self.proj(image)
        image = self.features(image)
        image = self.final_proj(image)
        # Flatten image to vector
        image = image.view(image.size(0), -1)
        return image
    
    def compute_fp(self, image_embd):
        return self.fp_classifier(image_embd)

    def forward(self, image, text=None, mem=None):
        if mem is None:
            image = self.compute_image(image)
            fp_out = self.compute_fp(image)

            image = image.unsqueeze(1)
            img_size = image.size(1)
            
            if text is None:
                # No text, so rely on image
                x = image
            else:
                text = self.embed(text)
                x = torch.cat((image, text), dim=1)
        else:
            # Use cached memory
            x = self.embed(text)

        x = self.dropout(x)
        x, new_mem = self.transformer(x, mem=mem)

        if mem is None:
            # Remove the image from output
            x = x[:, img_size - 1:]

        x = self.decoder(x)
        return x, fp_out, new_mem

def gelu(x):
    return x * torch.sigmoid(1.702 * x)

class GPT2Config(object):
    """Configuration class to store the configuration of a `GPT2Model`.
    """
    def __init__(
        self, vocab_size, n_positions, n_embd, n_ff,
        n_layer, n_head, activation=gelu, initializer_range=0.02,
        attention_mask=True):
        self.vocab_size = vocab_size
        self.n_positions = n_positions
        self.n_embd = n_embd
        self.n_ff = n_ff
        self.n_layer = n_layer
        self.n_head = n_head
        self.initializer_range = initializer_range
        self.activation = activation
        self.attention_mask = attention_mask

    @classmethod
    def from_dict(cls, json_object):
        """Constructs a `GPT2Config` from a Python dictionary of parameters."""
        config = GPT2Config(vocab_size_or_config_json_file=-1)
        for key, value in json_object.items():
            config.__dict__[key] = value
        return config

    @classmethod
    def from_json_file(cls, json_file):
        """Constructs a `GPT2Config` from a json file of parameters."""
        with open(json_file, "r", encoding="utf-8") as reader:
            text = reader.read()
        return cls.from_dict(json.loads(text))

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        """Serializes this instance to a Python dictionary."""
        output = copy.deepcopy(self.__dict__)
        return output

    def to_json_string(self):
        """Serializes this instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

class PositionalEmbedding(nn.Module):
    def __init__(self, demb):
        super(PositionalEmbedding, self).__init__()
        self.demb = demb
        inv_freq = 1 / (10000 ** (torch.arange(0.0, demb, 2.0) / demb))
        self.register_buffer('inv_freq', inv_freq)

    def forward(self, pos_seq):
        sinusoid_inp = torch.outer(pos_seq, self.inv_freq)
        pos_emb = torch.cat([sinusoid_inp.sin(), sinusoid_inp.cos()], dim=-1)
        return pos_emb[:,None,:]

class RelPartialLearnableMultiHeadAttn(nn.Module):
    def __init__(self, config):
        super().__init__()

        self.n_head = config.n_head
        self.n_embd = config.n_embd
        self.d_head = config.n_embd // config.n_head

        self.qkv_net = nn.Linear(self.n_embd, 3 * self.n_head * self.d_head)
        self.o_net = nn.Linear(self.n_head * self.d_head, self.n_embd)
        self.scale = 1 / (self.d_head ** 0.5)

        self.r_net = nn.Linear(self.n_embd, self.n_head * self.d_head, bias=False)
        self.r_r_bias = nn.Parameter(torch.Tensor(self.n_head, self.d_head))
        self.r_w_bias = nn.Parameter(torch.Tensor(self.n_head, self.d_head))
        nn.init.normal_(self.r_r_bias.data, 0.0, config.initializer_range / math.sqrt(config.n_layer))
        nn.init.normal_(self.r_w_bias.data, 0.0, config.initializer_range / math.sqrt(config.n_layer))

    def _rel_shift(self, x, zero_triu=False):
        zero_pad_shape = (x.size(0), 1) + x.size()[2:]
        zero_pad = torch.zeros(zero_pad_shape, device=x.device, dtype=x.dtype)
        x_padded = torch.cat([zero_pad, x], dim=1)

        x_padded_shape = (x.size(1) + 1, x.size(0)) + x.size()[2:]
        x_padded = x_padded.view(*x_padded_shape)

        x = x_padded[1:].view_as(x)

        if zero_triu:
            ones = torch.ones((x.size(0), x.size(1)))
            x = x * torch.tril(ones, x.size(1) - x.size(0))[:,:,None,None]
        return x

    def forward(self, w, r, attn_mask=None, mems=None):
        qlen, rlen, bsz = w.size(0), r.size(0), w.size(1)
        if mems is not None:
            print(w.size(), mems.size())
            # Compute new memory cache
            new_mems = torch.cat([mems, w], 0)
            w_heads = self.qkv_net(new_mems)
            r_head_k = self.r_net(r)

            w_head_q, w_head_k, w_head_v = torch.chunk(w_heads, 3, dim=-1)
            w_head_q = w_head_q[-qlen:]
        else:
            # Compute new memory cache
            new_mems = w

            w_heads = self.qkv_net(w)
            r_head_k = self.r_net(r)

            w_head_q, w_head_k, w_head_v = torch.chunk(w_heads, 3, dim=-1)

        klen = w_head_k.size(0)

        w_head_q = w_head_q.view(qlen, bsz, self.n_head, self.d_head)           # qlen x bsz x n_head x d_head
        w_head_k = w_head_k.view(klen, bsz, self.n_head, self.d_head)           # qlen x bsz x n_head x d_head
        w_head_v = w_head_v.view(klen, bsz, self.n_head, self.d_head)           # qlen x bsz x n_head x d_head

        r_head_k = r_head_k.view(rlen, self.n_head, self.d_head)                # qlen x n_head x d_head

        #### compute attention score
        rw_head_q = w_head_q + self.r_w_bias                                    # qlen x bsz x n_head x d_head
        AC = torch.einsum('ibnd,jbnd->ijbn', (rw_head_q, w_head_k))             # qlen x klen x bsz x n_head

        rr_head_q = w_head_q + self.r_r_bias
        BD = torch.einsum('ibnd,jnd->ijbn', (rr_head_q, r_head_k))              # qlen x klen x bsz x n_head
        BD = self._rel_shift(BD)

        # [qlen x klen x bsz x n_head]
        attn_score = AC + BD
        attn_score.mul_(self.scale)

        #### compute attention probability
        if attn_mask is not None and attn_mask.any().item():
            if attn_mask.dim() == 2:
                attn_score = attn_score.masked_fill(attn_mask[None,:,:,None], float('-inf'))
            elif attn_mask.dim() == 3:
                attn_score = attn_score.masked_fill(attn_mask[:,:,:,None], float('-inf'))

        # [qlen x klen x bsz x n_head]
        attn_prob = torch.softmax(attn_score.float(), dim=1).to(attn_score)

        #### compute attention vector
        attn_vec = torch.einsum('ijbn,jbnd->ibnd', (attn_prob, w_head_v))

        # Merge heads
        # [qlen x bsz x n_head x d_head]
        attn_vec = attn_vec.contiguous().view(attn_vec.size(0), attn_vec.size(1), self.n_head * self.d_head)

        ##### linear projection
        attn_out = self.o_net(attn_vec)
        return attn_out, new_mems

class MLP(nn.Module):
    def __init__(self, config):
        super(MLP, self).__init__()
        self.c_fc = nn.Linear(config.n_embd, config.n_ff)
        self.c_proj = nn.Linear(config.n_ff, config.n_embd)
        self.act = config.activation

    def forward(self, x):
        x = self.act(self.c_fc(x))
        x = self.c_proj(x)
        return x

class Block(nn.Module):
    def __init__(self, config):
        super(Block, self).__init__()
        self.ln_attn = nn.LayerNorm(config.n_embd)
        self.attn = RelPartialLearnableMultiHeadAttn(config)

        self.ln_ff = nn.LayerNorm(config.n_embd)
        self.mlp = MLP(config)

    def forward(self, x, pos_emb, attn_mask, mem=None):
        a, mem = self.attn(self.ln_attn(x), pos_emb, attn_mask, mems=mem)
        x += a

        m = self.mlp(self.ln_ff(x))
        x += m
        return x, mem

class GPT2BaseModel(nn.Module):
    def __init__(self, config, *inputs, **kwargs):
        super().__init__()
        self.config = config

    def init_weights(self, module):
        """ Initialize the weights.
        """
        if isinstance(module, (nn.Linear, nn.Embedding)):
            # Slightly different from the TF version which uses truncated_normal for initialization
            # cf https://github.com/pytorch/pytorch/pull/5617
            module.weight.data.normal_(mean=0.0, std=self.config.initializer_range / math.sqrt(self.config.n_layer))
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)
        if isinstance(module, nn.Linear) and module.bias is not None:
            module.bias.data.zero_()

class GPT2Model(GPT2BaseModel):
    def __init__(self, config):
        super(GPT2Model, self).__init__(config)
        self.pos_emb = PositionalEmbedding(config.n_embd)
        self.clamp_len = config.n_positions

        self.block = Block(config)
        self.ln_f = nn.LayerNorm(config.n_embd)

        self.apply(self.init_weights)

    def forward(self, inputs_embeds, mem=None):
        bzq, seq_len, _ = inputs_embeds.size()

        if mem is None:
            mem = [None] * self.config.n_layer

        mlen = mem[0][1].size(0) if mem[0] is not None else 0
        klen = mlen + seq_len

        # Compute positional embeddings
        pos_seq = torch.arange(klen - 1, -1, -1.0, device=inputs_embeds.device, dtype=inputs_embeds.dtype)
        if self.clamp_len > 0:
            pos_seq.clamp_(max=self.clamp_len)
        pos_emb = self.pos_emb(pos_seq)

        # Compute attention mask
        attn_mask = torch.triu(inputs_embeds.new_ones(seq_len, klen), diagonal=1 + mlen).bool()[:,:,None]

        hidden_states = inputs_embeds
        presents = []
        
        hidden_states = hidden_states.permute(1, 0, 2)
        for layer_mem in mem:
            hidden_states, present = self.block(hidden_states, pos_emb, attn_mask, layer_mem)
            presents.append(present)
        hidden_states = self.ln_f(hidden_states)
        hidden_states = hidden_states.permute(1, 0, 2)
        return hidden_states, presents