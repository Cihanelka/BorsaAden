"""
Created by: AdenBorsa ML Team
Created At: 2026-05-03
Subject: 15 modelli stratejik tahmin ve teknik analiz raporlama.
         Prompt 1-5 uyumlu: Pivot, S/R, Zone Encoding ve 15 model entegrasyonu.
"""

import os
import numpy as np
import pandas as pd
import joblib
from model_trainer import ModelTrainer, DL_MODELS_DIR, SUPPORTED_HORIZONS, HORIZON_LABELS, _modelPaths
from feature_engineer import prepareLiveFeatures, SEQUENCE_LENGTH
from news_collector import fetchCompanyNews
from sentiment_scorer import scoreNewsBatch

# TensorFlow (Opsiyonel yukleme)
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Etiketler
LABEL_FALL = -1
LABEL_STABLE = 0
LABEL_RISE = 1

VERDICT_EN = {LABEL_FALL: 'FALL', LABEL_STABLE: 'STABLE', LABEL_RISE: 'RISE'}
VERDICT_TR = {
    LABEL_FALL: 'dusebilir',
    LABEL_STABLE: 'sabit kalabilir',
    LABEL_RISE: 'yukselebilir',
}

class MonthlyPredictor:
    def __init__(self):
        # Her horizon icin ayri trainer
        self._trainers = {}
        self._dl_models = {}
        self._loaded_horizons = set()

        # Default trainer (geriye uyumluluk)
        self._trainer = None

    def loadModels(self) -> bool:
        """Tum horizon'lar icin modelleri yukler."""
        anyLoaded = False
        for h in SUPPORTED_HORIZONS:
            trainer = ModelTrainer(horizon=h)
            if trainer.load():
                self._trainers[h] = trainer
                self._loaded_horizons.add(h)
                anyLoaded = True
                print(f"  Modeller yuklendi: horizon={h} ({HORIZON_LABELS[h]['label']})")

                # DL modelleri
                if TF_AVAILABLE:
                    paths = _modelPaths(h)
                    for name in ['lstm', 'gru', 'cnn_1d']:
                        path = os.path.join(paths['dl_dir'], f"{name}.h5")
                        if os.path.exists(path):
                            try:
                                self._dl_models[(h, name)] = tf.keras.models.load_model(path)
                            except Exception as e:
                                print(f"  DL Model yukleme hatasi ({name}, h={h}): {e}")
            else:
                print(f"  Modeller bulunamadi: horizon={h}")

        # Geriye uyumluluk: ilk yuklenen trainer'i varsayilan yap
        if self._trainers:
            self._trainer = next(iter(self._trainers.values()))
        return anyLoaded

    @property
    def isLoaded(self) -> bool:
        return len(self._loaded_horizons) > 0

    @property
    def trainedAt(self) -> str:
        if self._trainer:
            return self._trainer.trainedAt
        return ""

    @property
    def availableHorizons(self) -> list:
        return sorted(self._loaded_horizons)

    def _getTrainer(self, horizon: int) -> ModelTrainer:
        """Istenen horizon icin trainer dondurur, yoksa en yakini secilir."""
        if horizon in self._trainers:
            return self._trainers[horizon]
        # En yakin horizon'u sec
        closest = min(self._trainers.keys(), key=lambda h: abs(h - horizon))
        return self._trainers[closest]

    def _alignFeaturesToTraining(self, liveRow: pd.Series, featureCols: list, trainer: ModelTrainer = None) -> pd.DataFrame:
        """
        Canli tahmin feature'larini egitimde kullanilan feature siralamasina hizalar.
        """
        t = trainer or self._trainer
        trainedFeatures = t.featureNames if t else []

        if not trainedFeatures:
            # Fallback: egitim feature isimleri yoksa mevcut siralama ile devam et
            return pd.DataFrame([liveRow[featureCols].fillna(0).values], columns=featureCols)

        alignedValues = {}
        for featName in trainedFeatures:
            if featName in liveRow.index:
                val = liveRow[featName]
                alignedValues[featName] = float(val) if pd.notna(val) else 0.0
            else:
                alignedValues[featName] = 0.0

        return pd.DataFrame([alignedValues])

    def predict(self, symbol: str, df: pd.DataFrame, fetchNews: bool = True, horizon: int = 5) -> dict:
        if not self.isLoaded:
            raise RuntimeError("Modeller yuklenmedi. train_models.py calistirin.")

        if len(df) < 250:
            raise ValueError("Yeterli veri yok. En az 250 gunluk veri gereklidir.")

        # Istenen horizon icin trainer sec
        trainer = self._getTrainer(horizon)
        actualHorizon = trainer.horizon

        # 1. Feature Hazirlama
        liveRow, fullFeatureDf, featureCols = prepareLiveFeatures(df)

        # KRITIK: Feature'lari egitim sirasindaki isim ve siraya hizala
        X_aligned = self._alignFeaturesToTraining(liveRow, featureCols, trainer)
        trainedFeatures = trainer.featureNames or featureCols

        # ML Modelleri icin Scale
        X_ml = trainer.scaler.transform(X_aligned)

        # 2. Oylama (Soft Voting - olasılık tabanlı)
        votes = {LABEL_FALL: 0, LABEL_STABLE: 0, LABEL_RISE: 0}
        individualVotes = {}

        # Olasılık ortalaması için toplam probabilities
        # Sınıf sırası: 0=FALL, 1=STABLE, 2=RISE (y+1 shift sonrası)
        allProbs = []

        # ML ve Ensemble Modelleri
        for name, model in trainer.models.items():
            if isinstance(model, str): continue # DL modelleri asagida
            try:
                # predict_proba ile olasılık dağılımını al
                if hasattr(model, 'predict_proba'):
                    probs = model.predict_proba(X_ml)[0]  # [P(class0), P(class1), P(class2)]
                    allProbs.append(probs)
                    pred_shifted = int(np.argmax(probs))
                else:
                    pred_shifted = int(model.predict(X_ml)[0])

                pred = pred_shifted - 1  # -1, 0, 1 formatina geri cevir
                votes[pred] += 1
                individualVotes[name] = VERDICT_EN[pred]
            except Exception as e:
                print(f"  Model tahmin hatasi ({name}): {e}")

        # DL Modelleri
        if TF_AVAILABLE:
            # Son 20 gunluk feature'lari al ve egitim sirasina hizala
            recentDf = fullFeatureDf[featureCols].tail(SEQUENCE_LENGTH).fillna(0)

            # Egitim feature sirasina hizala
            alignedRecent = pd.DataFrame(columns=trainedFeatures)
            for col in trainedFeatures:
                if col in recentDf.columns:
                    alignedRecent[col] = recentDf[col].values
                else:
                    alignedRecent[col] = 0.0

            X_seq = trainer.scaler.transform(alignedRecent)
            X_seq = X_seq.reshape(1, SEQUENCE_LENGTH, -1)

            for name in ['lstm', 'gru', 'cnn_1d']:
                key = (actualHorizon, name)
                if key not in self._dl_models:
                    continue
                model = self._dl_models[key]
                try:
                    probs = model.predict(X_seq, verbose=0)[0]
                    allProbs.append(probs)
                    pred_idx = np.argmax(probs)
                    pred = pred_idx - 1
                    votes[pred] += 1
                    individualVotes[name] = VERDICT_EN[pred]
                except Exception as e:
                    print(f"  DL Model tahmin hatasi ({name}): {e}")

        verdict = max(votes, key=votes.get)
        totalVotes = sum(votes.values())

        # Soft voting: Ortalama olasılık dağılımını hesapla
        avgProbabilities = {'fall': 0.0, 'stable': 0.0, 'rise': 0.0}
        if allProbs:
            avgProbs = np.mean(allProbs, axis=0)
            # Sınıf sırası: 0=FALL(shifted), 1=STABLE(shifted), 2=RISE(shifted)
            avgProbabilities = {
                'fall': round(float(avgProbs[0]), 4),
                'stable': round(float(avgProbs[1]), 4),
                'rise': round(float(avgProbs[2]), 4),
            }
            # Soft voting verdict: ortalama olasılığa göre karar
            probVerdictIdx = int(np.argmax(avgProbs))
            verdict = probVerdictIdx - 1  # 0,1,2 -> -1,0,1

        # 3. Teknik Gostergeler (Rapor icin)
        indicators = self._extractIndicators(fullFeatureDf, df)

        # 4. Haber Sentiment
        sentimentResult = {'total': 0, 'avg_score': 0.0, 'sentiment_label': 'NOTR'}
        if fetchNews:
            try:
                articles = fetchCompanyNews(symbol, days=30)
                if articles:
                    sentimentResult = scoreNewsBatch(articles)
            except: pass

        # 5. Aciklama Uretimi
        horizonLabel = HORIZON_LABELS.get(actualHorizon, {}).get('days', f'{actualHorizon} is gunu')
        explanation = self._generateExplanation(symbol, indicators, verdict, votes, totalVotes, sentimentResult, horizonLabel)

        return {
            'symbol': symbol,
            'verdict': VERDICT_EN[verdict],
            'verdict_tr': VERDICT_TR[verdict],
            'explanation': explanation,
            'model_votes': {
                'rise': votes[LABEL_RISE],
                'stable': votes[LABEL_STABLE],
                'fall': votes[LABEL_FALL],
                'total': totalVotes,
            },
            'avg_probabilities': avgProbabilities,
            'individual_model_votes': individualVotes,
            'sentiment': sentimentResult,
            'model_count': len(individualVotes),
            'trained_at': trainer.trainedAt,
            'horizon': actualHorizon,
            'horizon_label': HORIZON_LABELS.get(actualHorizon, {}).get('label', ''),
        }

    def _extractIndicators(self, featureDf: pd.DataFrame, rawDf: pd.DataFrame) -> dict:
        """Son satirdaki tum teknik gosterge degerlerini cikarir."""
        row = featureDf.iloc[-1]
        prevRow = featureDf.iloc[-2] if len(featureDf) > 1 else row

        def safeGet(col, default=0.0, src=row):
            val = src.get(col, default)
            return float(val) if pd.notna(val) else default

        close = round(float(rawDf['close'].iloc[-1]), 2)
        prevClose = round(float(rawDf['close'].iloc[-2]), 2) if len(rawDf) > 1 else close

        return {
            # Fiyat
            'close': close,
            'prev_close': prevClose,
            'daily_change_pct': round((close - prevClose) / (prevClose + 1e-10) * 100, 2),
            # RSI
            'rsi': round(safeGet('RSI_14', 50), 1),
            'rsi_zone': int(safeGet('RSI_zone', 0)),
            'rsi_prev': round(safeGet('RSI_14', 50, prevRow), 1),
            # MACD
            'macd_line': round(safeGet('MACD_line'), 4),
            'macd_signal': round(safeGet('MACD_signal'), 4),
            'macd_hist': round(safeGet('MACD_hist'), 4),
            'macd_hist_prev': round(safeGet('MACD_hist', 0, prevRow), 4),
            'macd_zone': int(safeGet('MACD_zone', 0)),
            # Bollinger
            'bb_pos': round(safeGet('BB_position', 0.5), 2),
            'bb_width': round(safeGet('BB_width', 0), 4),
            'bb_squeeze': int(safeGet('BB_squeeze', 0)),
            'bb_upper': round(safeGet('BB_upper', 0), 2),
            'bb_lower': round(safeGet('BB_lower', 0), 2),
            'bb_mid': round(safeGet('BB_mid', 0), 2),
            # Destek / Direnc
            'support': round(safeGet('support_level', 0), 2),
            'resistance': round(safeGet('resistance_level', 0), 2),
            'dist_support': round(safeGet('dist_to_support') * 100, 2),
            'dist_resist': round(safeGet('dist_to_resistance') * 100, 2),
            # Pivot
            'pivot_classic': round(safeGet('pivot_classic'), 2),
            'above_pivot': int(safeGet('above_pivot', 0)),
            'pivot_r1': round(safeGet('pivot_r1', 0), 2),
            'pivot_s1': round(safeGet('pivot_s1', 0), 2),
            # Hacim
            'volume_ratio': round(safeGet('volume_ratio', 1.0), 2),
            'obv_trend': int(safeGet('OBV_trend', 0)),
            # EMA
            'price_vs_ema20': round(safeGet('price_vs_EMA20') * 100, 2),
            'price_vs_ema50': round(safeGet('price_vs_EMA50') * 100, 2),
            'ema20_vs_ema50': round(safeGet('EMA20_vs_EMA50') * 100, 2),
            'ema_20': round(safeGet('EMA_20', 0), 2),
            'ema_50': round(safeGet('EMA_50', 0), 2),
            # Volatilite
            'atr_pct': round(safeGet('ATR_pct') * 100, 2),
            'atr_regime': int(safeGet('ATR_regime', 1)),
            # Confluence
            'net_confluence': int(safeGet('net_confluence', 0)),
            'bull_confluence': int(safeGet('bull_confluence', 0)),
            'bear_confluence': int(safeGet('bear_confluence', 0)),
            # Divergence
            'bull_divergence': int(safeGet('RSI_divergence_bull', 0)),
            'bear_divergence': int(safeGet('RSI_divergence_bear', 0)),
            # Mum yapisi
            'body_size': round(safeGet('body_size') * 100, 2),
            'is_bullish': int(safeGet('is_bullish_bar', 0)),
        }

    def _generateExplanation(self, symbol, ind, verdict, votes, totalVotes, sentiment, horizonLabel) -> str:
        """
        Her hisse icin gercek teknik verilere dayali, spesifik ve ikna edici
        bir analiz metni uretir. Model isim/sayilari kullaniciya gosterilmez.
        """
        sections = []

        close = ind['close']

        # ---- 1. TREND DURUMU (EMA Analizi) ----
        ema20vs50 = ind['ema20_vs_ema50']
        priceVsEma20 = ind['price_vs_ema20']

        if ema20vs50 > 1:
            sections.append(
                f"{symbol} hissesinde kısa vadeli hareketli ortalama (20 günlük EMA), "
                f"orta vadeli ortalamayı (50 günlük EMA) %{abs(ema20vs50):.1f} oranında yukarıda kesiyor; "
                f"bu güçlü bir yükseliş trendine işaret ediyor."
            )
        elif ema20vs50 < -1:
            sections.append(
                f"{symbol} hissesinde kısa vadeli hareketli ortalama (20 günlük EMA), "
                f"orta vadeli ortalamanın (50 günlük EMA) %{abs(ema20vs50):.1f} altında seyrediyor; "
                f"bu düşüş trendinin devam ettiğini gösteriyor."
            )
        else:
            sections.append(
                f"{symbol} hissesinde kısa ve orta vadeli hareketli ortalamalar birbirine yakın seyrediyor; "
                f"bu yatay bir seyir ve kararsızlık dönemine işaret ediyor."
            )

        # ---- 2. RSI ANALİZİ ----
        rsi = ind['rsi']
        rsiPrev = ind['rsi_prev']
        rsiDir = "yükselme" if rsi > rsiPrev else "düşme"

        if rsi > 70:
            sections.append(
                f"RSI göstergesi {rsi} seviyesinde ve aşırı alım bölgesinde bulunuyor. "
                f"Son işlem gününde RSI {rsiDir} eğiliminde olup, "
                f"kâr realizasyonu ve kısa vadeli düzeltme riski artmış durumda."
            )
        elif rsi > 60:
            sections.append(
                f"RSI göstergesi {rsi} seviyesinde ve güçlü bölgede. "
                f"Aşırı alım sınırına ({rsiDir} yönünde) yaklaşmakla birlikte, "
                f"momentum hâlâ alıcılar lehine."
            )
        elif rsi < 30:
            sections.append(
                f"RSI göstergesi {rsi} ile aşırı satım bölgesinde. "
                f"Bu seviye tarihsel olarak tepki alımlarının başlayabileceği bir nokta; "
                f"ancak düşüş trendi güçlüyse devam da edebilir."
            )
        elif rsi < 40:
            sections.append(
                f"RSI göstergesi {rsi} seviyesinde, zayıf bölgede. "
                f"Satıcı baskısı hâlâ hissediliyor ancak aşırı satım bölgesine henüz girilmedi."
            )
        else:
            sections.append(
                f"RSI göstergesi {rsi} seviyesinde ve nötr bölgede seyrediyor. "
                f"Bu aşamada ne alıcılar ne de satıcılar belirgin bir üstünlük sağlayamıyor."
            )

        # Divergence
        if ind['bull_divergence']:
            sections.append(
                "Dikkat çekici bir şekilde, fiyat yeni dip noktası oluştururken RSI daha yüksek bir dip yapmış durumda. "
                "Bu pozitif uyumsuzluk (bullish divergence), potansiyel bir trend dönüşü sinyali olarak değerlendiriliyor."
            )
        elif ind['bear_divergence']:
            sections.append(
                "Önemli bir teknik uyarı: Fiyat yeni tepe yaparken RSI'ın bu tepeyi onaylamaması (bearish divergence), "
                "yükseliş momentumunun zayıfladığına ve olası bir düzeltmeye işaret ediyor."
            )

        # ---- 3. MACD ANALİZİ ----
        macdHist = ind['macd_hist']
        macdHistPrev = ind['macd_hist_prev']
        macdLine = ind['macd_line']
        macdSignal = ind['macd_signal']

        if macdHist > 0 and macdHistPrev > 0:
            if macdHist > macdHistPrev:
                sections.append(
                    f"MACD histogram ({macdHist:.4f}) pozitif bölgede ve genişlemeye devam ediyor. "
                    f"MACD çizgisi ({macdLine:.4f}), sinyal çizgisinin ({macdSignal:.4f}) üzerinde; "
                    f"yükseliş momentumu güçleniyor."
                )
            else:
                sections.append(
                    f"MACD histogram ({macdHist:.4f}) pozitif olmakla birlikte daralmaya başlamış. "
                    f"Bu, yükseliş ivmesinin yavaşladığına dair erken bir uyarı olabilir."
                )
        elif macdHist < 0 and macdHistPrev < 0:
            if macdHist < macdHistPrev:
                sections.append(
                    f"MACD histogram ({macdHist:.4f}) negatif bölgede derinleşiyor. "
                    f"MACD çizgisi ({macdLine:.4f}), sinyal çizgisinin ({macdSignal:.4f}) altında; "
                    f"satış baskısı artıyor."
                )
            else:
                sections.append(
                    f"MACD histogram ({macdHist:.4f}) negatif olmakla birlikte toparlanma işareti veriyor. "
                    f"Düşüş momentumunun azalmaya başlaması, olası bir dönüş öncesi belirtisi olabilir."
                )
        elif macdHist > 0 and macdHistPrev <= 0:
            sections.append(
                f"MACD histogramı negatiften pozitife ({macdHist:.4f}) geçiş yapmış durumda. "
                f"Bu alım sinyali, kısa vadeli yükseliş beklentisini güçlendiriyor."
            )
        elif macdHist < 0 and macdHistPrev >= 0:
            sections.append(
                f"MACD histogramı pozitiften negatife ({macdHist:.4f}) dönmüş. "
                f"Bu satış sinyali, kısa vadeli düşüş baskısının başladığını gösteriyor."
            )

        # ---- 4. BOLLİNGER BANTLARI ----
        bbPos = ind['bb_pos']
        bbSqueeze = ind['bb_squeeze']
        bbUpper = ind['bb_upper']
        bbLower = ind['bb_lower']
        bbMid = ind['bb_mid']

        if bbSqueeze:
            sections.append(
                f"Bollinger bantları ciddi bir sıkışma (squeeze) sürecinde. "
                f"Bant genişliği son dönemin en dar seviyesine gerilemiş durumda. "
                f"Bu tür sıkışmalar genellikle sert bir fiyat hareketinin habercisidir; "
                f"kırılım yönü belirleyici olacak."
            )

        if bbPos > 0.95:
            sections.append(
                f"Fiyat ({close}$), üst Bollinger bandına ({bbUpper}$) çok yakın seyrediyor (pozisyon: %{bbPos*100:.0f}). "
                f"Üst banda bu denli yakınlık, kısa vadede geri çekilme ihtimalini artırıyor."
            )
        elif bbPos < 0.05:
            sections.append(
                f"Fiyat ({close}$), alt Bollinger bandına ({bbLower}$) dayanmış durumda (pozisyon: %{bbPos*100:.0f}). "
                f"Alt banddan seken fiyatlar genellikle orta banda ({bbMid}$) doğru bir toparlanma gösterir."
            )
        elif 0.4 <= bbPos <= 0.6:
            sections.append(
                f"Fiyat Bollinger bantlarının ortasında ({bbMid}$) dengeli bir konumda seyrediyor. "
                f"Bantlar arasındaki konum (%{bbPos*100:.0f}), belirgin bir aşırılık sinyali vermiyor."
            )

        # ---- 5. DESTEK / DİRENÇ & PİVOT ----
        support = ind['support']
        resistance = ind['resistance']
        pivot = ind['pivot_classic']
        distSupport = ind['dist_support']
        distResist = ind['dist_resist']

        if ind['above_pivot']:
            sections.append(
                f"Fiyat, günlük pivot seviyesinin ({pivot}$) üzerinde işlem görüyor. "
                f"Mevcut destek {support}$ (uzaklık: %{distSupport}), direnç ise {resistance}$ (uzaklık: %{distResist}) seviyesinde."
            )
        else:
            sections.append(
                f"Fiyat, günlük pivot seviyesinin ({pivot}$) altında kalmaya devam ediyor. "
                f"Destek seviyesi {support}$ (uzaklık: %{distSupport}), "
                f"direnç ise {resistance}$ (uzaklık: %{distResist}) olarak izleniyor."
            )

        # ---- 6. HACİM ANALİZİ ----
        volRatio = ind['volume_ratio']
        obvTrend = ind['obv_trend']

        if volRatio > 1.5:
            volDesc = "ortalamanın çok üzerinde" if volRatio > 2.0 else "ortalamanın üzerinde"
            sections.append(
                f"İşlem hacmi 20 günlük ortalamanın {volRatio:.1f} katı seviyesinde ({volDesc}). "
                f"Yüksek hacim, mevcut fiyat hareketinin güçlü bir katılımla desteklendiğini gösteriyor."
            )
        elif volRatio < 0.6:
            sections.append(
                f"İşlem hacmi ortalamanın oldukça altında ({volRatio:.1f}x). "
                f"Düşük hacimli hareketler genellikle güvenilirlikten yoksundur ve yanıltıcı olabilir."
            )

        if obvTrend == 1:
            sections.append("OBV (Denge Hacmi) göstergesi yukarı yönlü trend çiziyor; para akışı alıcılar lehine.")
        elif obvTrend == -1 and volRatio > 1.0:
            sections.append("OBV göstergesi aşağı yönlü trend çiziyor; hacim satış yönünde ağırlık kazanıyor.")

        # ---- 7. VOLATİLİTE ----
        atrPct = ind['atr_pct']
        atrRegime = ind['atr_regime']

        if atrRegime == 2:
            sections.append(
                f"Günlük ortalama oynaklık (ATR) %{atrPct:.1f} seviyesinde ve yüksek volatilite rejiminde. "
                f"Bu ortamda fiyat hareketleri daha sert ve öngörülemez olabilir."
            )
        elif atrRegime == 0:
            sections.append(
                f"Oynaklık (ATR: %{atrPct:.1f}) düşük seviyelerde; sakin bir piyasa ortamı hâkim. "
                f"Volatilite genellikle uzun süre düşük kalmaz; ani bir hareketin zemini hazırlanıyor olabilir."
            )

        # ---- 8. GENEL DEĞERLENDİRME ----
        verdictTr = VERDICT_TR[verdict]
        conf = ind['net_confluence']

        # Sentiment bilgisi (varsa)
        sentPart = ""
        sentTotal = sentiment.get('total', 0)
        if sentTotal > 0:
            sentLabel = sentiment.get('sentiment_label', 'NOTR')
            sentScore = sentiment.get('avg_score', 0)
            if sentLabel in ('POZİTİF', 'ÇOK POZİTİF'):
                sentPart = f" Piyasa haber akışı pozitif yönde ağırlıklı (skor: {sentScore:.2f}, {sentTotal} haber analiz edildi)."
            elif sentLabel in ('NEGATİF', 'ÇOK NEGATİF'):
                sentPart = f" Haber akışı negatif ağırlıklı (skor: {sentScore:.2f}, {sentTotal} haber), bu da ek temkinlilik gerektiriyor."
            else:
                sentPart = f" Haber akışı nötr bir görünüm sergiliyor ({sentTotal} haber analiz edildi)."

        # Confluence yorumu
        if conf >= 3:
            confText = f"Teknik göstergelerin çoğunluğu ({ind['bull_confluence']}/5 boğa sinyali) uyumlu bir yükseliş senaryosuna işaret ediyor."
        elif conf <= -3:
            confText = f"Göstergelerin büyük bölümü ({ind['bear_confluence']}/5 ayı sinyali) düşüş baskısını teyit ediyor."
        elif conf > 0:
            confText = "Teknik göstergeler hafif pozitif eğilimli olmakla birlikte güçlü bir konsensüs oluşmuş değil."
        elif conf < 0:
            confText = "Göstergeler hafif negatif eğilimli; ancak kesin bir yön belirleyemeyen karışık sinyaller mevcut."
        else:
            confText = "Teknik göstergeler arasında belirgin bir yön konsensüsü bulunmuyor; piyasa kararsız."

        conclusion = (
            f"\n\n<strong>Sonuç:</strong> {confText}{sentPart} "
            f"Tüm bu teknik veriler değerlendirildiğinde, {symbol} hissesinin "
            f"önümüzdeki {horizonLabel} içerisinde <strong>{verdictTr}</strong> eğiliminde olması bekleniyor."
        )

        return " ".join(sections) + conclusion

