import pandas as pd, numpy as np, config
class QuantitativeEnsembleModel:
    @staticmethod
    def _get_last(df,col):
        if col not in df.columns: return None
        s=df[col].dropna()
        return None if s.empty else s.iloc[-1]
    @staticmethod
    def evaluate_setup(df_m30,df_m15,df_m5,direction:str)->float:
        try:
            m5_c=QuantitativeEnsembleModel._get_last(df_m5,'close'); m5_k=QuantitativeEnsembleModel._get_last(df_m5,'kalman')
            m5_r=QuantitativeEnsembleModel._get_last(df_m5,'rsi'); m5_f=QuantitativeEnsembleModel._get_last(df_m5,'sma_fast')
            m5_s=QuantitativeEnsembleModel._get_last(df_m5,'sma_slow'); m5_m=QuantitativeEnsembleModel._get_last(df_m5,'macd')
            m5_ms=QuantitativeEnsembleModel._get_last(df_m5,'macd_signal'); m5_e=QuantitativeEnsembleModel._get_last(df_m5,'ema_50')
            m15_c=QuantitativeEnsembleModel._get_last(df_m15,'close'); m15_k=QuantitativeEnsembleModel._get_last(df_m15,'kalman')
            m15_f=QuantitativeEnsembleModel._get_last(df_m15,'sma_fast'); m15_s=QuantitativeEnsembleModel._get_last(df_m15,'sma_slow')
            m30_c=QuantitativeEnsembleModel._get_last(df_m30,'close'); m30_k=QuantitativeEnsembleModel._get_last(df_m30,'kalman')
            m30_f=QuantitativeEnsembleModel._get_last(df_m30,'sma_fast'); m30_s=QuantitativeEnsembleModel._get_last(df_m30,'sma_slow')
            if None in [m5_c,m5_k,m5_r,m5_f,m5_s,m30_c]: return 0.0
            score=0.0
            if direction=="BUY":
                if m30_c>m30_k: score+=0.15
                if m30_f and m30_s and m30_f>m30_s: score+=0.15
                if m15_c>m15_k: score+=0.10
                if m15_f and m15_s and m15_f>m15_s: score+=0.15
                if m5_c>m5_k: score+=0.10
                if m5_f>m5_s: score+=0.10
                if m5_e and m5_c>m5_e: score+=0.05
                if 45<=m5_r<=70: score+=0.10
                if m5_m and m5_ms and m5_m>m5_ms: score+=0.10
            else:
                if m30_c<m30_k: score+=0.15
                if m30_f and m30_s and m30_f<m30_s: score+=0.15
                if m15_c<m15_k: score+=0.10
                if m15_f and m15_s and m15_f<m15_s: score+=0.15
                if m5_c<m5_k: score+=0.10
                if m5_f<m5_s: score+=0.10
                if m5_e and m5_c<m5_e: score+=0.05
                if 30<=m5_r<=55: score+=0.10
                if m5_m and m5_ms and m5_m<m5_ms: score+=0.10
            return float(np.clip(score,0,1))
        except Exception as e: print(f"Ensemble err {direction} {e}"); return 0.0

class DynamicRiskManager:
    @staticmethod
    def calculate_levels(current_price: float, current_atr: float, direction: str) -> dict:
        atr=max(float(current_atr), config.MIN_SL_DISTANCE_USD/1.5)
        sl_dist=max(1.5*atr, config.MIN_SL_DISTANCE_USD)
        tp_dist=sl_dist*config.RRR_RATIO
        sl=current_price-sl_dist if direction=="BUY" else current_price+sl_dist
        tp=current_price+tp_dist if direction=="BUY" else current_price-tp_dist
        rrr=tp_dist/sl_dist if sl_dist>0 else 0
        return {"sl":round(float(sl),2),"tp":round(float(tp),2),"rrr_actual":round(float(rrr),2),"suggested_lot":0.01,"sl_distance":round(float(sl_dist),2)}
