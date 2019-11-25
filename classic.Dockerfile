#FROM pytorch/pytorch:1.0.1-cuda10.0-cudnn7-devel
FROM calclavia/smart:cli

RUN pip install celery
RUN pip install redis
RUN pip install matplotlib
RUN pip install pillow
RUN pip install sklearn
RUN pip install scikit-image
RUN pip install torchvision
RUN pip install requests
RUN pip install pandas

# RUN git clone https://github.com/nvidia/apex && \
#     cd apex && \
#     pip install -v --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" . && \
#     rm -rf apex

ADD . /src

WORKDIR /src

ENTRYPOINT []
