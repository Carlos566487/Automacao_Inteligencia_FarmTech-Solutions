class PredictionSystem:
    def __init__(self, model, monitor):
        self.model = model
        self.monitor = monitor
        self.prediction_cache = {}
        
    def predict_with_confidence(self, umidade, nutrientes):
        X = self._prepare_features(umidade, nutrientes)
        
        # Get prediction and probabilities
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        confidence = np.max(probabilities) * 100
        
        # Cache prediction for monitoring
        self._cache_prediction(umidade, nutrientes, prediction, confidence)
        
        return {
            'acao': prediction,
            'confianca': confidence,
            'probabilidades': dict(zip(self.model.classes_, probabilities))
        }
        
    def _prepare_features(self, umidade, nutrientes):
        # Prepare features for prediction
        return np.array([[
            umidade / 100.0,
            nutrientes / 10.0
        ]])
        
    def _cache_prediction(self, umidade, nutrientes, prediction, confidence):
        self.prediction_cache[datetime.now()] = {
            'umidade': umidade,
            'nutrientes': nutrientes,
            'prediction': prediction,
            'confidence': confidence
        }