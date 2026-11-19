import pandas as pd, joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from common import DATA, MODELS, REPORTS, write_json, rmse, wape
PATH=DATA/'yield'/'crop_yield.csv'; TARGET='hg/ha_yield'
def main():
    if not PATH.exists(): raise FileNotFoundError(f'Put CSV at {PATH}')
    df=pd.read_csv(PATH)
    required=['Area','Item','Year','average_rain_fall_mm_per_year','pesticides_tonnes','avg_temp',TARGET]
    missing=[c for c in required if c not in df]
    if missing: raise ValueError(f'Missing expected columns {missing}; found {list(df.columns)}')
    df=df[required].copy(); df[TARGET]=pd.to_numeric(df[TARGET],errors='coerce'); df['Year']=pd.to_numeric(df['Year'],errors='coerce')
    df=df.dropna(subset=[TARGET,'Year']); X=df.drop(columns=[TARGET]); y=df[TARGET]
    years=sorted(X.Year.unique())
    if len(years)>=5:
        cutoff=years[max(0,int(len(years)*.8)-1)]; tr=X.Year<=cutoff; te=X.Year>cutoff
        if tr.sum() and te.sum(): Xtr,Xte,ytr,yte=X.loc[tr],X.loc[te],y.loc[tr],y.loc[te]
        else: Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42)
    else: Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42)
    num=['Year','average_rain_fall_mm_per_year','pesticides_tonnes','avg_temp']; cat=['Area','Item']
    prep=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('scale',StandardScaler())]),num),
      ('cat',Pipeline([('imp',SimpleImputer(strategy='most_frequent')),('oh',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),cat)])
    candidates={'RandomForest':RandomForestRegressor(n_estimators=350,min_samples_leaf=2,random_state=42,n_jobs=-1),
      'ExtraTrees':ExtraTreesRegressor(n_estimators=350,min_samples_leaf=2,random_state=42,n_jobs=-1),
      'HistGradientBoosting':HistGradientBoostingRegressor(max_iter=250,learning_rate=.08,l2_regularization=.1,random_state=42)}
    results={}; fitted={}
    for name,est in candidates.items():
        pipe=Pipeline([('prep',prep),('model',est)]); pipe.fit(Xtr,ytr); pred=pipe.predict(Xte)
        results[name]={'MAE':float(mean_absolute_error(yte,pred)),'RMSE':rmse(yte,pred),'R2':float(r2_score(yte,pred)),
          'WAPE_percent':wape(yte,pred),'test_rows':int(len(yte))}
        fitted[name]=pipe
    winner=min(results,key=lambda k:results[k]['RMSE']); joblib.dump(fitted[winner],MODELS/'yield_regressor.joblib')
    write_json(REPORTS/'yield_metrics.json',{'winner':winner,'models':results,'features':list(X.columns),'target':TARGET,
      'split':'chronological latest-years holdout when possible'})
    print('Selected:',winner,results[winner])
if __name__=='__main__': main()
