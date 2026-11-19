import pandas as pd, joblib
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix
from common import DATA, MODELS, REPORTS, write_json
PATH=DATA/'crop_recommendation'/'Crop_recommendation.csv'
FEATURES=['N','P','K','temperature','humidity','ph','rainfall']; TARGET='label'
def main():
    if not PATH.exists(): raise FileNotFoundError(f'Put CSV at {PATH}')
    df=pd.read_csv(PATH)
    # Support datasets that use full-word column names (e.g. Nitrogen, Phosphorus, ... Crop)
    rename={}
    for src,dst in {'Nitrogen':'N','Phosphorus':'P','Potassium':'K','Temperature':'temperature',
        'Humidity':'humidity','pH_Value':'ph','Rainfall':'rainfall','Crop':'label'}.items():
        if dst not in df.columns and src in df.columns: rename[src]=dst
    if rename: df=df.rename(columns=rename)
    missing=[c for c in FEATURES+[TARGET] if c not in df]
    if missing: raise ValueError(f'Missing columns: {missing}; found {list(df.columns)}')
    df=df[FEATURES+[TARGET]].dropna(subset=[TARGET]); X=df[FEATURES]; y=df[TARGET].astype(str)
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
    models={
      'RandomForest':RandomForestClassifier(n_estimators=400,class_weight='balanced',random_state=42,n_jobs=-1),
      'ExtraTrees':ExtraTreesClassifier(n_estimators=400,class_weight='balanced',random_state=42,n_jobs=-1),
      'SVM_RBF':SVC(C=5,kernel='rbf',probability=True,class_weight='balanced',random_state=42),
      'HistGradientBoosting':HistGradientBoostingClassifier(max_iter=250,learning_rate=.08,random_state=42)}
    cv=StratifiedKFold(5,shuffle=True,random_state=42); results={}; fitted={}
    for name,est in models.items():
        pipe=Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',est)])
        scores=cross_validate(pipe,Xtr,ytr,cv=cv,scoring=['accuracy','f1_macro'],n_jobs=-1)
        pipe.fit(Xtr,ytr); pred=pipe.predict(Xte)
        pr,re,f1,_=precision_recall_fscore_support(yte,pred,average='macro',zero_division=0)
        results[name]={'cv_accuracy':float(scores['test_accuracy'].mean()),'cv_f1_macro':float(scores['test_f1_macro'].mean()),
          'test_accuracy':float(accuracy_score(yte,pred)),'test_precision_macro':float(pr),'test_recall_macro':float(re),
          'test_f1_macro':float(f1),'report':classification_report(yte,pred,output_dict=True,zero_division=0),
          'confusion_matrix':confusion_matrix(yte,pred,labels=sorted(y.unique())).tolist(),'class_order':sorted(y.unique())}
        fitted[name]=pipe
    winner=max(results,key=lambda k:results[k]['cv_f1_macro'])
    joblib.dump(fitted[winner],MODELS/'crop_recommender.joblib')
    write_json(REPORTS/'crop_metrics.json',{'winner':winner,'models':results,'features':FEATURES})
    print('Selected:',winner); print(pd.DataFrame(results).T[['cv_accuracy','cv_f1_macro','test_accuracy','test_f1_macro']])
if __name__=='__main__': main()
