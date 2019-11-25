test: 
	python ./SMART_FPinder.py input/cyclomarin_A_fenical_input.csv ./1.tsv ./1.png ./1-1.png

download_models:
	wget --output-document="models/HWK_sAug_1106_final(2048r1)_cos.hdf5" https://www.dropbox.com/s/9jjakvsjii8ut4c/HWK_sAug_1106_final%282048r1%29_cos.hdf5?dl=1
	wget --output-document="models/VGG16_high_aug_MW_continue.hdf5" https://www.dropbox.com/s/d9q5knhvhe7a32w/VGG16_high_aug_MW_continue.hdf5?dl=1

create_tf_from_keras:
	mkdir -p models/HWK_sAug_1106_final_2048_cos/000001
	python ../utilities/convert_keras_to_tf.py "models/HWK_sAug_1106_final(2048r1)_cos.hdf5" models/HWK_sAug_1106_final_2048_cos/000001

	mkdir -p models/VGG16_high_aug_MW_continue/000001
	python ../utilities/convert_keras_to_tf.py "models/VGG16_high_aug_MW_continue.hdf5" models/VGG16_high_aug_MW_continue/000001