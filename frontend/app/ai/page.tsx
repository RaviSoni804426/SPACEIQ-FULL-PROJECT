"use client";

import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Activity, BrainCircuit, Bot, TrendingUp, DollarSign, Database } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function AIDashboard() {
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState<{ role: "system" | "user" | "ai"; content: string }[]>([
    { role: "system", content: "AI Booking Assistant Initialized. Ask me for recommendations or predictions!" }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => {
    fetch(process.env.NEXT_PUBLIC_API_URL + "/ai/analytics")
      .then(res => res.json())
      .then(data => setAnalytics(data))
      .catch(err => console.error("Could not fetch analytics", err));
  }, []);

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    const currentInput = chatInput;
    setMessages(prev => [...prev, { role: "user", content: currentInput }]);
    setChatInput("");
    setIsTyping(true);

    try {
      const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: currentInput })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "ai", content: data.reply || "API Key Error" }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "system", content: "Error connecting to AI engine." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-8">
      <div className="flex items-center gap-3">
        <BrainCircuit className="h-8 w-8 text-orange-500" />
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Data Science & AI Hub</h1>
        <Badge variant="outline" className="ml-auto bg-orange-50 text-orange-600 border-orange-200">
          Powered by Pandas & Llama-3
        </Badge>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Chatbot Card */}
        <Card className="flex flex-col h-[500px] border-slate-200 shadow-sm">
          <CardHeader className="bg-slate-50 border-b pb-4">
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-indigo-500" />
              Smart Space Assistant
            </CardTitle>
            <CardDescription>NLP powered property recommendation agent</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-4 overflow-hidden gap-4">
            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${msg.role === "user" ? "bg-slate-900 text-white" : msg.role === "system" ? "bg-slate-100 text-slate-500 italic text-xs mx-auto" : "bg-orange-100 text-slate-900"}`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-orange-50 text-orange-400 rounded-2xl px-4 py-2 text-sm animate-pulse">
                    Thinking...
                  </div>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 pt-2 border-t">
              <Input
                placeholder="Ask about space availability, pricing..."
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSendMessage()}
              />
              <Button onClick={handleSendMessage}>Send</Button>
            </div>
          </CardContent>
        </Card>

        {/* Analytics Dashboard */}
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-4">
            <Card className="border-slate-200 bg-slate-50 shadow-none">
              <CardContent className="p-4 flex flex-col justify-center items-center h-full">
                <TrendingUp className="h-6 w-6 text-emerald-500 mb-2" />
                <p className="text-2xl font-bold">${analytics?.metrics?.predicted_next_day_revenue || 0}</p>
                <p className="text-xs text-slate-500 uppercase tracking-widest">Pred. Daily Rev</p>
              </CardContent>
            </Card>
            <Card className="border-slate-200 bg-slate-50 shadow-none">
              <CardContent className="p-4 flex flex-col justify-center items-center h-full">
                <Database className="h-6 w-6 text-blue-500 mb-2" />
                <p className="text-2xl font-bold">{analytics?.metrics?.total_bookings || 0}</p>
                <p className="text-xs text-slate-500 uppercase tracking-widest">Total Datapoints</p>
              </CardContent>
            </Card>
          </div>

          <Card className="flex-1 border-slate-200 shadow-sm flex flex-col">
            <CardHeader className="bg-slate-50 border-b pb-4">
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-rose-500" />
                Revenue Time-Series
              </CardTitle>
              <CardDescription>Pandas aggregated daily revenue pipeline</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 min-h-[250px] p-4">
              {analytics?.trend_data ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analytics.trend_data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" tick={{fontSize: 12}} />
                    <YAxis tick={{fontSize: 12}} />
                    <Tooltip />
                    <Line type="monotone" dataKey="total_amount" stroke="#f97316" strokeWidth={3} dot={{r: 4}} activeDot={{r: 6}} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full w-full flex items-center justify-center text-slate-400 text-sm">
                  Loading ML Analytics...
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
