import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { TrendingUp, BarChart3, Newspaper, LogOut, User, Star } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface AppHeaderProps {
  actions?: ReactNode;
  className?: string;
}

export const AppHeader = ({ actions, className }: AppHeaderProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  const navItems = [
    { to: "/", label: "Hisse Analizi", icon: BarChart3 },
    { to: "/favoriler", label: "Favorilerim", icon: Star },
    { to: "/haberler", label: "Haberler", icon: Newspaper },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <header
      className={cn(
        "relative z-10 border-b border-border/50 bg-background/80 backdrop-blur-sm",
        className
      )}
    >
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between gap-4">
          <Card
            className="border-border/50 bg-card/80 backdrop-blur-sm cursor-pointer"
            onClick={() => navigate("/")}
          >
            <CardContent className="py-3 px-4">
              <div className="flex items-center gap-3">
                <div className="h-14 w-14 rounded-full overflow-hidden shadow-lg border border-border/60">
                  <img
                    src="/1.ico"
                    alt="Aden Borsa Logo"
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-green-500 bg-clip-text text-transparent">
                    Aden Borsa
                  </h1>
                  <p className="text-sm text-muted-foreground">
                    Profesyonel Borsa Analiz Platformu
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex items-center gap-3 flex-wrap justify-end">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link key={item.to} to={item.to}>
                  <Button
                    variant={isActive(item.to) ? "default" : "ghost"}
                    className="gap-2"
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Button>
                </Link>
              );
            })}

            <div className="flex items-center gap-2 ml-1 pl-4 border-l border-border">
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-card/50">
                <User className="h-4 w-4 text-muted-foreground" />
                <Link to="/profil" className="text-sm font-medium hover:underline">
                  {user?.username ?? "Profil"}
                </Link>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={async () => {
                  await signOut();
                  navigate("/giris");
                }}
                title="Çıkış Yap"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {actions && <div className="mt-4">{actions}</div>}
      </div>
    </header>
  );
};
