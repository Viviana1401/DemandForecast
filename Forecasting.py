import matplotlib.pyplot as plt
import numpy as np
import pandas as pd 
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import numpy as np
from sklearn.metrics import *
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

def mean_absolute_percentage_error(y_true, y_pred): 
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

train=pd.read_csv('C:/Users/riard/Downloads/train.csv')
test=pd.read_csv("C:/Users/riard/Downloads/test.csv")
sample=pd.read_csv("C:/Users/riard/Downloads/sample_submission.csv")

train["year"] = pd.to_datetime(train["date"]).dt.year
train["month"] = pd.to_datetime(train["date"]).dt.month
train["day"] = pd.to_datetime(train["date"]).dt.day
train['dayOfWeek'] =  pd.to_datetime(train["date"]).dt.dayofweek

train.head()

test.head()

sample.head()

df=train[train['store']==1][train['item']==1]
df.shape

df["sales"] = np.log1p(df["sales"])

df = df[["date", "sales"]]

df=df.rename(columns={"date":"ds","sales":"y"})

df.ds=pd.to_datetime(df.ds,format='%Y-%m')

m = Prophet()
m.fit(df)
future = m.make_future_dataframe(periods=365)
future.tail()

forecast = m.predict(future)
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()

preds= forecast['yhat'][:-365]

plt.figure(figsize=(15,6))
plt.plot(df.ds,preds,color='red',label=' Predictions')
plt.plot(df.ds,df.y,color='yellow',label='Actual')
plt.legend()
plt.show()

r2 = round(r2_score(df["y"], preds), 3)
mse = round(mean_squared_error(df["y"], preds), 3)
mae = round(mean_absolute_error(df["y"], preds), 3)
print("R2: ", r2)
print("MSE: ", mse)
print("MAE: ", mae)

fig1 = m.plot(forecast)
fig1.set_size_inches(15,6)

fig2 = m.plot_components(forecast)
plt.show()

# las ventas son de lunes a domingo y en julio hay un pico // incluir holidays, partidos NFL (domingos)

    
playoffs = ['2013-07-12', '2014-07-12', '2014-07-19',
                 '2014-07-02', '2015-07-11', '2016-07-17',
                 '2016-07-24', '2016-07-07','2016-07-24']
superbowl = ['2013-01-01', '2013-12-25', '2014-01-01', '2014-12-25','2015-01-01', '2015-12-25','2016-01-01', '2016-12-25',
                '2017-01-01', '2017-12-25']

playoffs = pd.DataFrame({
  'holiday': 'playoff',
  'ds': pd.to_datetime(playoffs),
  'lower_window': 0,
  'upper_window': 1,
})
superbowls = pd.DataFrame({
  'holiday': 'superbowl',
  'ds': pd.to_datetime(superbowl),
  'lower_window': 0,
  'upper_window': 1,
})
holidays = pd.concat((playoffs, superbowls))

df["dow"] = pd.to_datetime(train["date"]).dt.day_name() # dia de la semana (day of week)
df.head()

def nfl_sunday(ds):
    date = pd.to_datetime(ds)
    if date.weekday() == 6 and (date.month > 8 or date.month < 2):
        return 1
    else:
        return 0

df =df[["ds", 'y']]
df.head()

df["nfl_sunday"] = df['ds'].apply(nfl_sunday)
df

m = Prophet(holidays=holidays, holidays_prior_scale=0.5,
            yearly_seasonality=4,  interval_width=0.95,
            changepoint_prior_scale=0.006, daily_seasonality=True)
m.add_regressor('nfl_sunday')
m.add_seasonality(name='daily', period=60, fourier_order=5)
m.fit(df)

future = m.make_future_dataframe(periods=90, freq="D") # Daily frequency
future['nfl_sunday'] = future['ds'].apply(nfl_sunday)
future.head()

forecast=m.predict(future)

preds= forecast['yhat'][:-90]

plt.figure(figsize=(15,6))
plt.plot(df.ds,preds,color='red',label=' Predictions')
plt.plot(df.ds,df.y,color='yellow',label='Actual')
plt.legend()
plt.show()

r2 = round(r2_score(df["y"], preds), 3)
mse = round(mean_squared_error(df["y"], preds), 3)
mae = round(mean_absolute_error(df["y"], preds), 3)
print("R2: ", r2)
print("MSE: ", mse)
print("MAE: ", mae)

fig1 = m.plot(forecast)

fig2 = m.plot_components(forecast)
plt.show()

future.tail()

ps1i1 = forecast[["ds"]]
ps1i1["forecast"] = np.expm1(forecast["yhat"])
ps1i1["yearmonth"] = pd.to_datetime(ps1i1["ds"]).dt.to_period("M")
ps1i1.head()

def smape(outsample, forecast):
    num = np.abs(outsample-forecast)
    denom = np.abs(outsample) + np.abs(forecast)
    return (num/denom)/2

df["ds"] = pd.to_datetime(df["ds"])

ps1i1["ds"] = pd.to_datetime(ps1i1["ds"])

train_predict = df.merge(ps1i1)

smape_err = smape(train_predict["y"], train_predict["forecast"])
smape_err = smape_err[~np.isnan(smape_err)]
np.mean(smape_err)

