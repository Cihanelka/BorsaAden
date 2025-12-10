import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { BackgroundChart } from "@/components/BackgroundChart";
import { TrendingUp, BarChart3, Newspaper, LogOut, User, Star, Save, Eye, EyeOff, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export default function Profile() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  
  const [username, setUsername] = useState(user?.username || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setUsername(user.username || '');
    }
  }, [user]);

  const handleUpdateProfile = async () => {
    if (!username.trim()) {
      toast.error('Kullanıcı adı boş olamaz');
      return;
    }

    if (username.length < 3) {
      toast.error('Kullanıcı adı en az 3 karakter olmalı');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:3001/api/auth/update-profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ username })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Güncelleme başarısız');
      }

      toast.success('Kullanıcı adı güncellendi');
      // Update the displayed username without page reload
      if (user) {
        user.username = username;
      }
    } catch (error: any) {
      toast.error(error.message || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error('Tüm alanları doldurun');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('Yeni şifre en az 6 karakter olmalı');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('Yeni şifreler eşleşmiyor');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:3001/api/auth/change-password', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ currentPassword, newPassword })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Şifre değiştirilemedi');
      }

      toast.success('Şifre başarıyla değiştirildi');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      toast.error(error.message || 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <BackgroundChart />
      
      {/* Header */}
      <header className="relative z-10 border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div
              className="flex items-center gap-3 cursor-pointer"
              onClick={() => navigate('/')}
            >
              <div className="h-10 w-10 bg-gradient-primary rounded-lg flex items-center justify-center shadow-glow">
                <TrendingUp className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-chart-secondary bg-clip-text text-transparent">
                  Aden Borsa
                </h1>
                <p className="text-sm text-muted-foreground">
                  Profesyonel Borsa Analiz Platformu
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Link to="/">
                <Button 
                  variant={location.pathname === "/" ? "default" : "ghost"}
                  className="gap-2"
                >
                  <BarChart3 className="h-4 w-4" />
                  <span>Hisse Analizi</span>
                </Button>
              </Link>
              <Link to="/favoriler">
                <Button 
                  variant={location.pathname === "/favoriler" ? "default" : "ghost"}
                  className="gap-2"
                >
                  <Star className="h-4 w-4" />
                  <span>Favorilerim</span>
                </Button>
              </Link>
              <Link to="/haberler">
                <Button 
                  variant={location.pathname === "/haberler" ? "default" : "ghost"}
                  className="gap-2"
                >
                  <Newspaper className="h-4 w-4" />
                  <span>Haberler</span>
                </Button>
              </Link>
              
              <div className="flex items-center gap-2 ml-4 pl-4 border-l border-border">
                <Link to="/profil">
                  <Button
                    variant={location.pathname === "/profil" ? "default" : "ghost"}
                    className="gap-2"
                  >
                    <User className="h-4 w-4" />
                    <span>{user?.username}</span>
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={async () => {
                    await signOut();
                    navigate('/giris');
                  }}
                  title="Çıkış Yap"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-foreground mb-2">
              Profil Ayarları
            </h2>
            <p className="text-muted-foreground">
              Hesap bilgilerinizi yönetin
            </p>
          </div>

          <div className="space-y-6">
            {/* Profil Bilgileri */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle>Profil Bilgileri</CardTitle>
                <CardDescription>
                  Kullanıcı adınızı güncelleyebilirsiniz
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="username">Kullanıcı Adı</Label>
                  <Input
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Kullanıcı adınız"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">E-posta</Label>
                  <Input
                    id="email"
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="bg-muted"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    E-posta adresiniz değiştirilemez
                  </p>
                </div>

                <Button
                  onClick={handleUpdateProfile}
                  disabled={loading || !username || username === user?.username}
                  className="w-full"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Kullanıcı Adını Güncelle
                </Button>
              </CardContent>
            </Card>

            {/* Şifre Değiştirme */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle>Şifre Değiştir</CardTitle>
                <CardDescription>
                  Hesabınızın güvenliği için güçlü bir şifre kullanın
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Mevcut Şifre</Label>
                  <Input
                    id="currentPassword"
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="••••••••"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="newPassword">Yeni Şifre</Label>
                  <div className="relative">
                    <Input
                      id="newPassword"
                      type={showNewPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="••••••••"
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full hover:bg-transparent"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                    >
                      {showNewPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Yeni Şifre (Tekrar)</Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showNewPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full hover:bg-transparent"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                    >
                      {showNewPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <Button
                  onClick={handleChangePassword}
                  disabled={loading || !currentPassword || !newPassword || newPassword !== confirmPassword}
                  className="w-full"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Şifreyi Değiştir
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <footer className="relative z-10 border-t border-border/50 bg-background/80 backdrop-blur-sm mt-20">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              © 2025 Aden Borsa. Tüm Hakları Saklıdır.
            </p>
            <p className="text-xs text-muted-foreground">
              Bu Platform Yatırım Tavsiyesi Vermez. Kendi Riskinizi Değerlendirin.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
