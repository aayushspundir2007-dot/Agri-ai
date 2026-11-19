"""CNN-based Plant Disease classifier (TensorFlow / Keras).

This is the original deep-learning trainer. It requires TensorFlow, which has
no wheels for Python 3.14 — run it under Python 3.10 or 3.11 (see README).

    python src/train_disease_cnn.py   # on Python 3.10/3.11 with tensorflow installed

It expects class subfolders of images under data/plant_disease. The active
trainer used by the app on Python 3.14 is train_disease.py (scikit-learn).
"""
import json, tensorflow as tf
from common import DATA, MODELS, REPORTS, write_json
IMG=(224,224); BATCH=32; SEED=42
def main():
    folder=DATA/'plant_disease'
    if not folder.exists() or not any(p.is_dir() for p in folder.iterdir()):
        raise FileNotFoundError(f'Arrange images in class subfolders under {folder}')
    train=tf.keras.utils.image_dataset_from_directory(folder,validation_split=.2,subset='training',seed=SEED,image_size=IMG,batch_size=BATCH)
    val=tf.keras.utils.image_dataset_from_directory(folder,validation_split=.2,subset='validation',seed=SEED,image_size=IMG,batch_size=BATCH)
    classes=train.class_names; autotune=tf.data.AUTOTUNE; train=train.prefetch(autotune); val=val.prefetch(autotune)
    aug=tf.keras.Sequential([tf.keras.layers.RandomFlip('horizontal'),tf.keras.layers.RandomRotation(.08),tf.keras.layers.RandomZoom(.1)])
    base=tf.keras.applications.MobileNetV2(input_shape=IMG+(3,),include_top=False,weights='imagenet'); base.trainable=False
    inp=tf.keras.Input(shape=IMG+(3,)); x=aug(inp); x=tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x=base(x,training=False); x=tf.keras.layers.GlobalAveragePooling2D()(x); x=tf.keras.layers.Dropout(.3)(x)
    out=tf.keras.layers.Dense(len(classes),activation='softmax')(x); model=tf.keras.Model(inp,out)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),loss='sparse_categorical_crossentropy',metrics=['accuracy'])
    callbacks=[tf.keras.callbacks.EarlyStopping(patience=4,restore_best_weights=True,monitor='val_loss'),
      tf.keras.callbacks.ModelCheckpoint(str(MODELS/'disease_classifier.keras'),save_best_only=True,monitor='val_loss')]
    hist=model.fit(train,validation_data=val,epochs=15,callbacks=callbacks)
    (MODELS/'disease_classes.json').write_text(json.dumps(classes,indent=2))
    write_json(REPORTS/'disease_metrics.json',{'classes':classes,'best_validation_accuracy':float(max(hist.history['val_accuracy'])),
      'epochs_run':len(hist.history['loss']),'note':'Use plant/field-group split where metadata permits; random image split may overestimate generalization.'})
    print('Saved image model for',len(classes),'classes')
if __name__=='__main__': main()
