import { useEffect } from 'react';

export const BackgroundChart = () => {
  useEffect(() => {
    // CSS animasyonları ekle
    const style = document.createElement('style');
    style.textContent = `
      @keyframes float1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(30px, -50px) scale(1.1); }
        66% { transform: translate(-20px, 20px) scale(0.9); }
      }
      
      @keyframes float2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(-40px, 30px) scale(0.9); }
        66% { transform: translate(20px, -40px) scale(1.1); }
      }
      
      @keyframes float3 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(20px, 40px) scale(1.05); }
        66% { transform: translate(-30px, -20px) scale(0.95); }
      }
      
      @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
      }
      
      .bg-blob-1 {
        animation: float1 20s ease-in-out infinite;
      }
      
      .bg-blob-2 {
        animation: float2 25s ease-in-out infinite;
      }
      
      .bg-blob-3 {
        animation: float3 22s ease-in-out infinite;
      }
      
      .bg-gradient-animated {
        background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #667eea);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
      }
    `;
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <>
      {/* Ana arka plan - Modern gradient */}
      <div className="fixed inset-0 z-0 bg-gradient-animated opacity-30" />
      
      {/* Animasyonlu blob'lar - Glassmorphism efekti */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        {/* Blob 1 - Mor */}
        <div
          className="bg-blob-1 absolute rounded-full blur-3xl opacity-20"
          style={{
            width: '400px',
            height: '400px',
            background: 'radial-gradient(circle, #667eea 0%, transparent 70%)',
            top: '-100px',
            left: '-100px',
          }}
        />
        
        {/* Blob 2 - Pembe */}
        <div
          className="bg-blob-2 absolute rounded-full blur-3xl opacity-20"
          style={{
            width: '500px',
            height: '500px',
            background: 'radial-gradient(circle, #f093fb 0%, transparent 70%)',
            bottom: '-150px',
            right: '-100px',
          }}
        />
        
        {/* Blob 3 - Koyu Mor */}
        <div
          className="bg-blob-3 absolute rounded-full blur-3xl opacity-15"
          style={{
            width: '350px',
            height: '350px',
            background: 'radial-gradient(circle, #764ba2 0%, transparent 70%)',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
        />
      </div>
      
      {/* Yumuşak overlay - Derinlik ve kontrast */}
      <div
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(circle at 20% 50%, rgba(102, 126, 234, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(240, 147, 251, 0.05) 0%, transparent 50%),
            linear-gradient(to bottom, rgba(0, 0, 0, 0.1) 0%, transparent 50%, rgba(0, 0, 0, 0.05) 100%)
          `
        }}
      />
    </>
  );
};