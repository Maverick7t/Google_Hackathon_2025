import React, { useState, useEffect } from 'react';
import { Send, BarChart3, MessageSquare, TrendingUp, AlertCircle, Clock } from 'lucide-react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import ReactMarkdown from 'react-markdown';
import logo from './assets/logo.jpg.png';
import { API_BASE_URL } from './config';

const DevInsight = () => {
    const [activeTab, setActiveTab] = useState('chat');
    const [messages, setMessages] = useState([
        { id: 1, type: 'ai', text: "Hello! I'm your AI Analyst for GitHub. Ask me anything about your team's code." },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    // State for reports data
    const [reportStats, setReportStats] = useState({
        closed: 0,
        open: 0,
        avgResolution: 0,
        topContributor: '',
        topCommits: 0
    });
    const [contributorData, setContributorData] = useState([]);
    const [issueStats, setIssueStats] = useState([
        { name: 'Closed', value: 0, fill: '#06B6D4' },
        { name: 'Open', value: 0, fill: '#0EA5E9' },
    ]);
    const [recentIssues, setRecentIssues] = useState([]);
    const [blockers, setBlockers] = useState([]);

    const suggestedQueries = [
        "Who contributed the most?",
        "Recent closed issues",
        "What's blocking us?",
        "Top repositories",
    ];

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = { id: messages.length + 1, type: 'user', text: input };
        setMessages([...messages, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE_URL}/ask`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: input })
            });

            const data = await res.json();

            const aiResponse = {
                id: messages.length + 2,
                type: 'ai',
                text: data.answer || "No data found.",
            };
            setMessages((prev) => [...prev, aiResponse]);
        } catch (error) {
            console.error("❌ Chat error:", error);
            setMessages((prev) => [
                ...prev,
                { id: messages.length + 2, type: 'ai', text: "Server error. Try again later." },
            ]);
        } finally {
            setLoading(false);
        }
    };

    // 🧠 Fetch real analytics for Reports tab
    useEffect(() => {
        const fetchReports = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/reports`);
                const data = await res.json();
                console.log("📊 Report data:", data);

                if (!data) return;

                // Top contributor from backend
                const top = data.contributors?.[0] || {};

                setReportStats({
                    closed: data.issues?.closed || 0,
                    open: data.issues?.open || 0,
                    avgResolution: data.issues?.avg_resolution_hrs?.toFixed(1) || 0,
                    topContributor: top.name || 'N/A',
                    topCommits: top.commits || 0
                });

                setContributorData(data.contributors || []);

                // Ensure both open and closed issues are shown
                const closedCount = data.issues?.closed || 0;
                const openCount = data.issues?.open || 0;

                console.log("📊 Issue counts - Closed:", closedCount, "Open:", openCount);

                setIssueStats([
                    { name: 'Closed', value: closedCount, fill: '#22c55e' },
                    { name: 'Open', value: openCount, fill: '#eab308' }
                ]);
                setBlockers(data.blockers || []);

                // Fetch recent issues
                const recentRes = await fetch(`${API_BASE_URL}/issues/recent`);
                const recentData = await recentRes.json();
                setRecentIssues(recentData.recent_issues || []);

            } catch (err) {
                console.error('❌ Failed to load reports:', err);
            }
        };
        fetchReports();
    }, []);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', backgroundColor: '#0f172a', color: 'white', overflow: 'hidden', fontFamily: 'system-ui, -apple-system, sans-serif' }}>

            {/* Animated Background */}
            <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', overflow: 'hidden', zIndex: 0 }}>
                <div style={{ position: 'absolute', top: 0, right: 0, width: '300px', height: '300px', background: 'rgba(147, 51, 234, 0.1)', borderRadius: '50%', filter: 'blur(80px)', animation: 'pulse 4s ease-in-out infinite' }}></div>
                <div style={{ position: 'absolute', bottom: 0, left: 0, width: '300px', height: '300px', background: 'rgba(34, 197, 234, 0.1)', borderRadius: '50%', filter: 'blur(80px)', animation: 'pulse 4s ease-in-out infinite 1s' }}></div>
            </div>

            {/* Main Content Container */}
            <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>

                {/* Header - Always Fixed */}
                <header style={{ flexShrink: 0, borderBottom: '1px solid rgba(99, 102, 241, 0.2)', backdropFilter: 'blur(4px)', backgroundColor: 'rgba(15, 23, 42, 0.8)', padding: window.innerWidth < 640 ? '12px 16px' : '16px 24px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: window.innerWidth < 768 ? '12px' : '32px' }}>

                        {/* Logo */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                            <img
                                src={logo}
                                alt="DevInsight Logo"
                                style={{
                                    width: window.innerWidth < 640 ? '32px' : '40px',
                                    height: window.innerWidth < 640 ? '32px' : '40px',
                                    borderRadius: '8px',
                                    objectFit: 'cover'
                                }}
                            />
                            <h1 style={{ fontWeight: 'bold', fontSize: window.innerWidth < 640 ? '18px' : (window.innerWidth < 1024 ? '20px' : '24px'), margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>DevInsight</h1>
                        </div>

                        {/* Tabs - Center */}
                        <div style={{ display: 'flex', gap: '8px', background: 'rgba(30, 41, 59, 0.5)', padding: '6px', borderRadius: '8px' }}>
                            {['chat', 'reports'].map((tab) => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: window.innerWidth < 640 ? '6px' : '8px',
                                        padding: window.innerWidth < 640 ? '8px 12px' : '10px 16px',
                                        borderRadius: '6px',
                                        border: 'none',
                                        backgroundColor: activeTab === tab ? '#0891b2' : 'transparent',
                                        color: activeTab === tab ? 'white' : '#94a3b8',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        fontSize: window.innerWidth < 640 ? '12px' : '14px',
                                        fontWeight: '500',
                                        boxShadow: activeTab === tab ? '0 0 20px rgba(6, 182, 212, 0.3)' : 'none',
                                    }}
                                    onMouseEnter={(e) => !activeTab === tab && (e.target.style.backgroundColor = 'rgba(99, 102, 241, 0.1)')}
                                    onMouseLeave={(e) => !activeTab === tab && (e.target.style.backgroundColor = 'transparent')}
                                >
                                    {tab === 'chat' ? <MessageSquare size={16} style={{ flexShrink: 0 }} /> : <BarChart3 size={16} style={{ flexShrink: 0 }} />}
                                    {window.innerWidth >= 640 && <span>{tab.charAt(0).toUpperCase() + tab.slice(1)}</span>}
                                </button>
                            ))}
                        </div>

                        {/* Empty spacer to balance the grid */}
                        <div></div>

                        {/* Avatar
                        <div style={{ width: window.innerWidth < 640 ? '32px' : '40px', height: window.innerWidth < 640 ? '32px' : '40px', background: 'linear-gradient(135deg, #c084fc, #ec4899)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: window.innerWidth < 640 ? '12px' : '14px', flexShrink: 0 }}>
                            AI
                        </div> */}
                    </div>
                </header>

                {/* Content Area - Flexible */}
                <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

                    {/* CHAT TAB */}
                    {activeTab === 'chat' && (
                        <div style={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column' }}>

                            {/* Messages Container */}
                            <div style={{ flex: 1, overflowY: 'auto', padding: window.innerWidth < 640 ? '16px' : '24px', display: 'flex', flexDirection: 'column' }}>
                                <div style={{ maxWidth: '48rem', margin: '0 auto', width: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>

                                    {messages.length <= 1 ? (
                                        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: window.innerWidth < 640 ? '24px' : '32px', padding: '32px 16px' }}>
                                            <div style={{ textAlign: 'center' }}>
                                                <h2 style={{ fontSize: window.innerWidth < 640 ? '24px' : (window.innerWidth < 1024 ? '28px' : '36px'), fontWeight: 'bold', marginBottom: '8px', margin: 0 }}>Welcome to DevInsight</h2>
                                                <p style={{ color: '#94a3b8', fontSize: window.innerWidth < 640 ? '14px' : '16px', margin: 0 }}>Ask questions about your GitHub activity</p>
                                            </div>

                                            <div style={{ display: 'grid', gridTemplateColumns: window.innerWidth < 640 ? '1fr' : '1fr 1fr', gap: window.innerWidth < 640 ? '8px' : '12px', width: '100%', maxWidth: '320px' }}>
                                                {suggestedQueries.map((query, idx) => (
                                                    <button
                                                        key={idx}
                                                        onClick={() => setInput(query)}
                                                        style={{
                                                            padding: '12px 16px',
                                                            backgroundColor: 'rgba(30, 41, 59, 0.5)',
                                                            border: '1px solid rgba(71, 85, 105, 0.5)',
                                                            borderRadius: '8px',
                                                            cursor: 'pointer',
                                                            fontSize: window.innerWidth < 640 ? '12px' : '14px',
                                                            color: '#cbd5e1',
                                                            transition: 'all 0.2s',
                                                            minHeight: '56px',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            textAlign: 'center',
                                                        }}
                                                        onMouseEnter={(e) => {
                                                            e.target.style.backgroundColor = 'rgba(30, 41, 59, 0.8)';
                                                            e.target.style.borderColor = '#06B6D4';
                                                            e.target.style.color = '#06B6D4';
                                                        }}
                                                        onMouseLeave={(e) => {
                                                            e.target.style.backgroundColor = 'rgba(30, 41, 59, 0.5)';
                                                            e.target.style.borderColor = 'rgba(71, 85, 105, 0.5)';
                                                            e.target.style.color = '#cbd5e1';
                                                        }}
                                                    >
                                                        {query}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    ) : (
                                        messages.map((msg) => (
                                            <div key={msg.id} style={{ display: 'flex', justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start', animation: 'fadeIn 0.3s ease-out' }}>
                                                <div
                                                    className="message-content"
                                                    style={{
                                                        maxWidth: window.innerWidth < 640 ? '85%' : '400px',
                                                        padding: '12px 16px',
                                                        borderRadius: '8px',
                                                        fontSize: window.innerWidth < 640 ? '12px' : '14px',
                                                        lineHeight: '1.5',
                                                        wordWrap: 'break-word',
                                                        backgroundColor: msg.type === 'user' ? 'rgba(6, 182, 212, 0.8)' : 'rgba(30, 41, 59, 0.8)',
                                                        border: msg.type === 'user' ? 'none' : '1px solid rgba(71, 85, 105, 0.5)',
                                                        borderBottomRightRadius: msg.type === 'user' ? '0px' : '8px',
                                                        borderBottomLeftRadius: msg.type === 'user' ? '8px' : '0px',
                                                    }}
                                                >
                                                    <ReactMarkdown
                                                        components={{
                                                            p: ({ children }) => <p style={{ margin: '0.5em 0' }}>{children}</p>,
                                                            ul: ({ children }) => <ul style={{ marginLeft: '1.5em', marginTop: '0.5em', marginBottom: '0.5em' }}>{children}</ul>,
                                                            ol: ({ children }) => <ol style={{ marginLeft: '1.5em', marginTop: '0.5em', marginBottom: '0.5em' }}>{children}</ol>,
                                                            li: ({ children }) => <li style={{ margin: '0.3em 0' }}>{children}</li>,
                                                            a: ({ href, children }) => (
                                                                <a
                                                                    href={href}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    style={{ color: '#06B6D4', textDecoration: 'underline' }}
                                                                >
                                                                    {children}
                                                                </a>
                                                            ),
                                                            code: ({ children }) => (
                                                                <code style={{
                                                                    backgroundColor: 'rgba(0, 0, 0, 0.3)',
                                                                    padding: '2px 6px',
                                                                    borderRadius: '4px',
                                                                    fontSize: '0.9em'
                                                                }}>
                                                                    {children}
                                                                </code>
                                                            ),
                                                            strong: ({ children }) => <strong style={{ fontWeight: '600' }}>{children}</strong>,
                                                            blockquote: ({ children }) => (
                                                                <blockquote style={{
                                                                    borderLeft: '3px solid #06B6D4',
                                                                    paddingLeft: '1em',
                                                                    marginLeft: '0',
                                                                    fontStyle: 'italic',
                                                                    color: '#94a3b8'
                                                                }}>
                                                                    {children}
                                                                </blockquote>
                                                            ),
                                                        }}
                                                    >
                                                        {msg.text}
                                                    </ReactMarkdown>
                                                </div>
                                            </div>
                                        ))
                                    )}

                                    {loading && (
                                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-start' }}>
                                            <div style={{ backgroundColor: 'rgba(30, 41, 59, 0.8)', border: '1px solid rgba(71, 85, 105, 0.5)', borderRadius: '8px', borderBottomLeftRadius: '0px', padding: '12px 16px', display: 'flex', gap: '4px' }}>
                                                <div style={{ width: '8px', height: '8px', backgroundColor: '#06B6D4', borderRadius: '50%', animation: 'bounce 1.4s ease-in-out infinite' }}></div>
                                                <div style={{ width: '8px', height: '8px', backgroundColor: '#06B6D4', borderRadius: '50%', animation: 'bounce 1.4s ease-in-out infinite 0.1s' }}></div>
                                                <div style={{ width: '8px', height: '8px', backgroundColor: '#06B6D4', borderRadius: '50%', animation: 'bounce 1.4s ease-in-out infinite 0.2s' }}></div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Input Area - Fixed at Bottom */}
                            <div style={{ flexShrink: 0, borderTop: '1px solid rgba(99, 102, 241, 0.2)', backgroundColor: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(4px)', padding: window.innerWidth < 640 ? '12px 16px' : '16px 24px' }}>
                                <div style={{ maxWidth: '48rem', margin: '0 auto', display: 'flex', gap: window.innerWidth < 640 ? '8px' : '12px' }}>
                                    <input
                                        type="text"
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                                        placeholder="Ask about GitHub..."
                                        style={{
                                            flex: 1,
                                            backgroundColor: 'rgba(30, 41, 59, 0.5)',
                                            border: '1px solid rgba(71, 85, 105, 0.5)',
                                            borderRadius: '8px',
                                            padding: window.innerWidth < 640 ? '8px 12px' : '10px 16px',
                                            fontSize: window.innerWidth < 640 ? '12px' : '14px',
                                            color: 'white',
                                            outline: 'none',
                                            transition: 'all 0.2s',
                                            boxSizing: 'border-box',
                                        }}
                                        onFocus={(e) => (e.target.style.borderColor = '#06B6D4')}
                                        onBlur={(e) => (e.target.style.borderColor = 'rgba(71, 85, 105, 0.5)')}
                                    />
                                    <button
                                        onClick={handleSend}
                                        disabled={!input.trim() || loading}
                                        style={{
                                            backgroundColor: input.trim() && !loading ? '#0891b2' : '#475569',
                                            cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                                            padding: window.innerWidth < 640 ? '8px 12px' : '10px 16px',
                                            borderRadius: '8px',
                                            border: 'none',
                                            color: 'white',
                                            transition: 'all 0.2s',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            flexShrink: 0,
                                        }}
                                    >
                                        <Send size={18} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* REPORTS TAB */}
                    {activeTab === 'reports' && (
                        <div
                            style={{
                                height: '100%',
                                width: '100%',
                                overflowY: 'auto',
                                padding: window.innerWidth < 640 ? '16px' : '24px',
                            }}
                        >
                            <div
                                style={{
                                    maxWidth: '90rem',
                                    margin: '0 auto',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: window.innerWidth < 640 ? '16px' : '24px',
                                    paddingBottom: '24px',
                                }}
                            >
                                {/* 🔹 Quick Stats Section */}
                                <div
                                    style={{
                                        display: 'grid',
                                        gridTemplateColumns:
                                            window.innerWidth < 640
                                                ? '1fr'
                                                : window.innerWidth < 1024
                                                    ? '1fr 1fr'
                                                    : '1fr 1fr 1fr',
                                        gap: window.innerWidth < 640 ? '12px' : '16px',
                                    }}
                                >
                                    {[
                                        { label: 'Closed Issues', value: `${reportStats.closed}`, unit: 'closed total' },
                                        { label: 'Avg Resolution', value: `${reportStats.avgResolution}h`, unit: 'created → closed' },
                                        { label: 'Top Contributor', value: reportStats.topContributor, unit: `${reportStats.topCommits} commits` },
                                    ].map((stat, idx) => (
                                        <div
                                            key={idx}
                                            style={{
                                                backgroundColor: 'rgba(30, 41, 59, 0.5)',
                                                border: '1px solid rgba(71, 85, 105, 0.5)',
                                                borderRadius: '8px',
                                                padding: window.innerWidth < 640 ? '16px' : '20px',
                                            }}
                                        >
                                            <div style={{ color: '#94a3b8', fontSize: window.innerWidth < 640 ? '12px' : '14px', marginBottom: '8px' }}>
                                                {stat.label}
                                            </div>
                                            <div style={{ fontSize: window.innerWidth < 640 ? '24px' : '28px', fontWeight: 'bold', color: '#06B6D4', marginBottom: '4px' }}>
                                                {stat.value}
                                            </div>
                                            <div style={{ fontSize: '12px', color: '#64748b' }}>{stat.unit}</div>
                                        </div>
                                    ))}
                                </div>

                                {/* 🔹 Charts Section */}
                                <div
                                    style={{
                                        display: 'grid',
                                        gridTemplateColumns: window.innerWidth < 1024 ? '1fr' : '1fr 1fr',
                                        gap: window.innerWidth < 640 ? '12px' : '24px',
                                    }}
                                >
                                    {/* Top Contributors Bar Chart */}
                                    <div
                                        style={{
                                            backgroundColor: 'rgba(30, 41, 59, 0.5)',
                                            border: '1px solid rgba(71, 85, 105, 0.5)',
                                            borderRadius: '8px',
                                            padding: window.innerWidth < 640 ? '16px' : '20px',
                                            minHeight: '320px',
                                        }}
                                    >
                                        <h3 style={{ fontSize: window.innerWidth < 640 ? '14px' : '16px', fontWeight: '600', marginBottom: '16px', margin: 0 }}>
                                            Top Contributors
                                        </h3>
                                        <ResponsiveContainer width="100%" height={280}>
                                            <BarChart data={contributorData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                                <XAxis dataKey="name" stroke="#94A3B8" fontSize={12} />
                                                <YAxis stroke="#94A3B8" fontSize={12} />
                                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }} />
                                                <Bar dataKey="commits" fill="#06B6D4" radius={[8, 8, 0, 0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>

                                    {/* Issue Status Pie Chart */}
                                    <div
                                        style={{
                                            backgroundColor: 'rgba(30, 41, 59, 0.5)',
                                            border: '1px solid rgba(71, 85, 105, 0.5)',
                                            borderRadius: '8px',
                                            padding: window.innerWidth < 640 ? '16px' : '20px',
                                            minHeight: '320px',
                                        }}
                                    >
                                        <h3
                                            style={{
                                                fontSize: window.innerWidth < 640 ? '14px' : '16px',
                                                fontWeight: '600',
                                                marginBottom: '16px',
                                                margin: 0,
                                            }}
                                        >
                                            Issue Status
                                        </h3>
                                        <ResponsiveContainer width="100%" height={280}>
                                            <PieChart>
                                                <Pie
                                                    data={issueStats}
                                                    cx="50%"
                                                    cy="50%"
                                                    innerRadius={60}
                                                    outerRadius={90}
                                                    dataKey="value"
                                                    paddingAngle={5}
                                                    label={({ name, value, percent }) =>
                                                        `${name}: ${value} (${(percent * 100).toFixed(1)}%)`
                                                    }
                                                    labelLine={{
                                                        stroke: '#94a3b8',
                                                        strokeWidth: 1
                                                    }}
                                                >
                                                    {issueStats.map((entry, idx) => (
                                                        <Cell
                                                            key={`cell-${idx}`}
                                                            fill={entry.fill}
                                                            stroke={entry.fill}
                                                            strokeWidth={2}
                                                        />
                                                    ))}
                                                </Pie>
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: '#1e293b',
                                                        border: '1px solid #475569',
                                                        borderRadius: '8px',
                                                        color: '#ffffff',
                                                        padding: '10px',
                                                    }}
                                                    itemStyle={{ color: '#ffffff' }}
                                                    formatter={(value, name) => [`${value} issues`, name]}
                                                />
                                                <Legend
                                                    verticalAlign="bottom"
                                                    height={36}
                                                    iconType="circle"
                                                    formatter={(value, entry) => (
                                                        <span style={{ color: '#ffffff', fontSize: '14px' }}>
                                                            {value}: {entry.payload.value}
                                                        </span>
                                                    )}
                                                />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>

                                </div>

                                {/* 🔹 Recent Issues & Blockers */}
                                <div
                                    style={{
                                        display: 'grid',
                                        gridTemplateColumns: window.innerWidth < 1024 ? '1fr' : '1fr 1fr',
                                        gap: window.innerWidth < 640 ? '12px' : '24px',
                                    }}
                                >
                                    {/* Recent Issues */}
                                    <div
                                        style={{
                                            backgroundColor: 'rgba(30, 41, 59, 0.5)',
                                            border: '1px solid rgba(71, 85, 105, 0.5)',
                                            borderRadius: '8px',
                                            padding: window.innerWidth < 640 ? '16px' : '20px',
                                        }}
                                    >
                                        <h3 style={{ fontSize: window.innerWidth < 640 ? '14px' : '16px', fontWeight: '600', marginBottom: '12px', margin: 0 }}>
                                            Recent Issues
                                        </h3>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                            {(recentIssues || []).slice(0, 5).map((issue, idx) => (
                                                <div
                                                    key={idx}
                                                    style={{
                                                        backgroundColor: 'rgba(55, 65, 81, 0.2)',
                                                        padding: '10px',
                                                        borderRadius: '6px',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s',
                                                    }}
                                                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(55, 65, 81, 0.4)')}
                                                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(55, 65, 81, 0.2)')}
                                                >
                                                    <div
                                                        style={{
                                                            fontSize: window.innerWidth < 640 ? '12px' : '13px',
                                                            color: '#cbd5e1',
                                                            fontWeight: '500',
                                                            marginBottom: '4px',
                                                        }}
                                                    >
                                                        {issue.title || 'No title'}
                                                    </div>
                                                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                                        <span
                                                            style={{
                                                                padding: '2px 6px',
                                                                borderRadius: '4px',
                                                                fontSize: '11px',
                                                                fontWeight: '600',
                                                                backgroundColor: issue.state === 'open' ? 'rgba(234, 179, 8, 0.25)' : 'rgba(34, 197, 94, 0.25)',
                                                                color: issue.state === 'open' ? '#eab308' : '#22c55e',
                                                            }}
                                                        >
                                                            {issue.state || 'unknown'}
                                                        </span>
                                                        <span
                                                            style={{
                                                                fontSize: '11px',
                                                                color: '#94a3b8',
                                                                backgroundColor: 'rgba(71, 85, 105, 0.5)',
                                                                padding: '2px 6px',
                                                                borderRadius: '4px',
                                                            }}
                                                        >
                                                            {issue.repo_name || 'N/A'}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                            {(recentIssues || []).length === 0 && (
                                                <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>No recent issues found</p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Blockers */}
                                    <div
                                        style={{
                                            backgroundColor: 'rgba(30, 41, 59, 0.5)',
                                            border: '1px solid rgba(71, 85, 105, 0.5)',
                                            borderRadius: '8px',
                                            padding: window.innerWidth < 640 ? '16px' : '20px',
                                        }}
                                    >
                                        <h3
                                            style={{
                                                fontSize: window.innerWidth < 640 ? '14px' : '16px',
                                                fontWeight: '600',
                                                marginBottom: '16px',
                                                margin: 0,
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '8px',
                                            }}
                                        >
                                            <AlertCircle size={16} color="#f87171" style={{ flexShrink: 0 }} />
                                            Blockers
                                        </h3>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: window.innerWidth < 640 ? '8px' : '12px' }}>
                                            {(blockers || []).length > 0 ? (
                                                (blockers || []).map((blocker, idx) => (
                                                    <div
                                                        key={idx}
                                                        style={{
                                                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                                            borderLeft: '4px solid #ef4444',
                                                            padding: '12px',
                                                            borderRadius: '6px',
                                                            transition: 'all 0.2s',
                                                            cursor: 'pointer',
                                                        }}
                                                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.2)')}
                                                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)')}
                                                    >
                                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '6px' }}>
                                                            <span
                                                                style={{
                                                                    padding: '2px 8px',
                                                                    backgroundColor: 'rgba(239, 68, 68, 0.25)',
                                                                    color: '#fca5a5',
                                                                    fontSize: '11px',
                                                                    fontWeight: 'bold',
                                                                    borderRadius: '4px',
                                                                    whiteSpace: 'nowrap',
                                                                }}
                                                            >
                                                                [BUG]
                                                            </span>
                                                            <span
                                                                style={{
                                                                    fontSize: '11px',
                                                                    color: '#94a3b8',
                                                                    backgroundColor: 'rgba(71, 85, 105, 0.5)',
                                                                    padding: '2px 8px',
                                                                    borderRadius: '4px',
                                                                }}
                                                            >
                                                                {blocker.repo_name || 'N/A'}
                                                            </span>
                                                        </div>
                                                        <p style={{ fontSize: window.innerWidth < 640 ? '12px' : '14px', color: '#e2e8f0', margin: 0 }}>
                                                            {blocker.title || 'No title'}
                                                        </p>
                                                    </div>
                                                ))
                                            ) : (
                                                <p style={{ fontSize: '14px', color: '#94a3b8' }}>No blockers found</p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                </div>
            </div>

            <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        body {
          margin: 0;
          padding: 0;
        }
      `}</style>
        </div>
    );
};

export default DevInsight;