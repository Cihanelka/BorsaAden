// src/lib/aiCommentaryModel.ts
import * as tf from '@tensorflow/tfjs';

// Define input data interface (based on TechnicalAnalysis levels)
interface TechnicalData {
  rsi: number;
  macd: number;
  bollingerUpper: number;
  bollingerLower: number;
  support1: number;
  resistance1: number;
  currentPrice: number;
}

// Simple commentary labels (can be expanded)
enum CommentaryLabel {
  BULLISH = 'Bullish: Yükseliş eğilimi görülüyor, alım fırsatı olabilir.',
  BEARISH = 'Bearish: Düşüş riski var, dikkatli olun.',
  NEUTRAL = 'Neutral: Piyasa dengeli, bekle-gör stratejisi uygula.',
  OVERBOUGHT = 'Overbought: Aşırı alım, satış sinyali.',
  OVERSOLD = 'Oversold: Aşırı satım, alım sinyali.'
}

class AICommentaryModel {
  private model: tf.Sequential | null = null;
  private isTrained = false;

  // Initialize the model
  async initialize() {
    this.model = tf.sequential({
      layers: [
        tf.layers.dense({ inputShape: [6], units: 10, activation: 'relu' }), // Input: 6 features (RSI, MACD, etc.)
        tf.layers.dense({ units: 5, activation: 'softmax' }) // Output: 5 commentary labels
      ]
    });
    this.model.compile({
      optimizer: 'adam',
      loss: 'sparseCategoricalCrossentropy',
      metrics: ['accuracy']
    });
  }

  // Train the model with sample data (expand with real API data)
  async train() {
    if (!this.model) await this.initialize();
    const sampleInputs = tf.tensor2d([
      [75, 0.5, 100, 80, 90, 95], // Overbought example
      [25, -0.5, 120, 100, 110, 105], // Oversold example
      [50, 0, 110, 90, 100, 100], // Neutral example
      [80, 1, 105, 85, 95, 100], // Bullish example
      [20, -1, 115, 95, 105, 100] // Bearish example
    ]);
    const sampleLabels = tf.tensor1d([3, 4, 2, 0, 1], 'int32'); // Corresponding to CommentaryLabel indices
    await this.model!.fit(sampleInputs, sampleLabels, { epochs: 50, verbose: 0 });
    this.isTrained = true;
  }

  // Predict commentary based on technical data
  async predict(data: TechnicalData): Promise<string> {
    if (!this.model || !this.isTrained) {
      await this.train(); // Train if not done
    }
    const input = tf.tensor2d([[data.rsi, data.macd, data.bollingerUpper, data.bollingerLower, data.support1, data.resistance1]]);
    const prediction = this.model!.predict(input) as tf.Tensor;
    const labelIndex = (await prediction.argMax(1).data())[0];
    return CommentaryLabel[labelIndex] || CommentaryLabel.NEUTRAL;
  }
}

// Export a singleton instance
export const aiCommentaryModel = new AICommentaryModel();