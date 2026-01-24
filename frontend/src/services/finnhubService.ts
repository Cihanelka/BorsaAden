const FINNHUB_API_KEY = import.meta.env.VITE_FINNHUB_KEY || 'demo';
const BASE_URL = 'https://finnhub.io/api/v1';

export interface CompanyProfile {
  country: string;
  currency: string;
  exchange: string;
  ipo: string;
  marketCapitalization: number;
  name: string;
  phone: string;
  shareOutstanding: number;
  ticker: string;
  weburl: string;
  logo: string;
  finnhubIndustry: string;
}

export interface FinancialReport {
  symbol: string;
  cik: string;
  year: number;
  quarter: number;
  form: string;
  startDate: string;
  endDate: string;
  filedDate: string;
  acceptedDate: string;
  report: {
    bs?: Array<{
      label: string;
      concept: string;
      unit: string;
      value: number;
    }>;
    ic?: Array<{
      label: string;
      concept: string;
      unit: string;
      value: number;
    }>;
    cf?: Array<{
      label: string;
      concept: string;
      unit: string;
      value: number;
    }>;
  };
}

export interface FinancialsResponse {
  data: FinancialReport[];
}

export const getCompanyProfile = async (symbol: string): Promise<CompanyProfile> => {
  try {
    if (FINNHUB_API_KEY === 'demo' || !FINNHUB_API_KEY) {
      throw new Error('Finnhub API key bulunamadı. Lütfen .env dosyasında VITE_FINNHUB_KEY değişkenini tanımlayın.');
    }

    const response = await fetch(
      `${BASE_URL}/stock/profile2?symbol=${symbol}&token=${FINNHUB_API_KEY}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch company profile');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching company profile:', error);
    throw error;
  }
};

export const getFinancialReports = async (symbol: string): Promise<FinancialsResponse> => {
  try {
    if (FINNHUB_API_KEY === 'demo' || !FINNHUB_API_KEY) {
      throw new Error('Finnhub API key bulunamadı. Lütfen .env dosyasında VITE_FINNHUB_KEY değişkenini tanımlayın.');
    }

    const response = await fetch(
      `${BASE_URL}/stock/financials-reported?symbol=${symbol}&token=${FINNHUB_API_KEY}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch financial reports');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching financial reports:', error);
    throw error;
  }
};

export const getCompanyNews = async (symbol: string, from: string, to: string) => {
  try {
    if (FINNHUB_API_KEY === 'demo' || !FINNHUB_API_KEY) {
      throw new Error('Finnhub API key bulunamadı. Lütfen .env dosyasında VITE_FINNHUB_KEY değişkenini tanımlayın.');
    }

    const response = await fetch(
      `${BASE_URL}/company-news?symbol=${symbol}&from=${from}&to=${to}&token=${FINNHUB_API_KEY}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch company news');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching company news:', error);
    throw error;
  }
};
