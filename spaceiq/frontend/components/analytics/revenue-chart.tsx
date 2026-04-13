"use client";

import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { RevenuePoint } from "@/types";

const COLORS = ["#F97316", "#FB923C", "#FDBA74", "#38BDF8", "#22C55E", "#8B5CF6"];

export function RevenueBarChart({ data }: { data: RevenuePoint[] }) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="space_name" hide />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
            {data.map((item, index) => (
              <Cell fill={COLORS[index % COLORS.length]} key={item.space_name} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BookingTypeDonut({ data }: { data: RevenuePoint[] }) {
  const aggregate = Object.values(
    data.reduce<Record<string, { name: string; value: number }>>((acc, item) => {
      const key = item.space_type;
      acc[key] = acc[key] ?? { name: key.replace("_", " "), value: 0 };
      acc[key].value += item.value;
      return acc;
    }, {}),
  );

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={aggregate} dataKey="value" innerRadius={70} outerRadius={100} paddingAngle={6}>
            {aggregate.map((entry, index) => (
              <Cell fill={COLORS[index % COLORS.length]} key={entry.name} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
