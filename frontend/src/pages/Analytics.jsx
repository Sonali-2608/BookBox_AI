import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { Flame, BookCheck, BookMarked, Heart } from "lucide-react";
import { userApi } from "../services/api.js";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";

export default function Analytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    let cancelled = false;
    userApi
      .getAnalytics()
      .then((res) => !cancelled && setData(res.data))
      .catch(() => !cancelled && setData(null));
    return () => {
      cancelled = true;
    };
  }, []);

  if (!data) {
    return (
      <div className="mx-auto max-w-6xl">
        <span className="eyebrow">Analytics</span>
        <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
          Your reading, by the numbers.
        </h1>
        <div className="mt-8">
          <LoadingSkeleton count={4} />
        </div>
      </div>
    );
  }

  const stats = [
    { label: "Completed", value: data.books_completed, icon: BookCheck },
    { label: "Currently reading", value: data.currently_reading, icon: BookMarked },
    { label: "Want to read", value: data.want_to_read, icon: Heart },
    { label: "Reading streak", value: `${data.reading_streak_days} days`, icon: Flame },
  ];

  return (
    <div className="mx-auto max-w-6xl">
      <span className="eyebrow">Analytics</span>
      <h1 className="mt-2 font-display text-3xl font-medium text-parchment">
        Your reading, by the numbers.
      </h1>

      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="catalog-card p-5">
            <s.icon className="h-5 w-5 text-moss-dark/60" strokeWidth={1.5} />
            <p className="mt-2 font-display text-2xl font-medium text-parchment-ink">
              {s.value}
            </p>
            <p className="call-number mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <h2 className="font-display text-lg font-medium text-parchment">
            Books completed per month
          </h2>
          <div className="catalog-card mt-4 p-5">
            {data.monthly_activity.length === 0 ? (
              <p className="py-8 text-center text-sm text-parchment-ink/50">
                Complete a book to start seeing activity here.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data.monthly_activity}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(29,25,48,0.08)" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#1D1930" }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#1D1930" }} />
                  <Tooltip />
                  <Bar dataKey="completed" fill="#C9A15C" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <h2 className="font-display text-lg font-medium text-parchment">Favorite genres</h2>
            <div className="catalog-card mt-4 p-5">
              {data.favorite_genres.length === 0 ? (
                <p className="text-sm text-parchment-ink/50">
                  Track a few books to see your top genres.
                </p>
              ) : (
                <ul className="space-y-2">
                  {data.favorite_genres.map((g) => (
                    <li key={g.name} className="flex items-center justify-between text-sm">
                      <span className="text-parchment-ink/80">{g.name}</span>
                      <span className="call-number">{g.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div>
            <h2 className="font-display text-lg font-medium text-parchment">Favorite authors</h2>
            <div className="catalog-card mt-4 p-5">
              {data.favorite_authors.length === 0 ? (
                <p className="text-sm text-parchment-ink/50">
                  Track a few books to see your top authors.
                </p>
              ) : (
                <ul className="space-y-2">
                  {data.favorite_authors.map((a) => (
                    <li key={a.name} className="flex items-center justify-between text-sm">
                      <span className="text-parchment-ink/80">{a.name}</span>
                      <span className="call-number">{a.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
