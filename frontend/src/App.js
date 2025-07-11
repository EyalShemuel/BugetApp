import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const App = () => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [summary, setSummary] = useState({});
  const [newTransaction, setNewTransaction] = useState({
    amount: '',
    type: 'expense',
    category: '',
    description: '',
    date: new Date().toISOString().split('T')[0]
  });
  const [aiMessages, setAiMessages] = useState([]);
  const [aiInput, setAiInput] = useState('');
  const [aiSessionId] = useState(() => 'session_' + Date.now());
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [householdComparison, setHouseholdComparison] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [transactionsRes, categoriesRes, monthlyRes, summaryRes, comparisonRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/transactions`),
        fetch(`${API_BASE_URL}/api/categories`),
        fetch(`${API_BASE_URL}/api/stats/monthly`),
        fetch(`${API_BASE_URL}/api/stats/summary`),
        fetch(`${API_BASE_URL}/api/comparison/household`)
      ]);

      const transactionsData = await transactionsRes.json();
      const categoriesData = await categoriesRes.json();
      const monthlyData = await monthlyRes.json();
      const summaryData = await summaryRes.json();
      const comparisonData = await comparisonRes.json();

      setTransactions(transactionsData.transactions || []);
      setCategories(categoriesData.categories || []);
      setMonthlyStats(monthlyData.monthly_stats || []);
      setSummary(summaryData);
      setHouseholdComparison(comparisonData);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const handleSubmitTransaction = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/api/transactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newTransaction),
      });

      if (response.ok) {
        setNewTransaction({
          amount: '',
          type: 'expense',
          category: '',
          description: '',
          date: new Date().toISOString().split('T')[0]
        });
        fetchData();
      }
    } catch (error) {
      console.error('Error creating transaction:', error);
    }
  };

  const handleAiChat = async (e) => {
    e.preventDefault();
    if (!aiInput.trim()) return;

    setIsAiLoading(true);
    setAiMessages(prev => [...prev, { type: 'user', message: aiInput }]);
    const userMessage = aiInput;
    setAiInput('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: aiSessionId,
          message: userMessage
        }),
      });

      const data = await response.json();
      setAiMessages(prev => [...prev, { type: 'ai', message: data.response }]);
    } catch (error) {
      console.error('Error with AI chat:', error);
      setAiMessages(prev => [...prev, { type: 'ai', message: 'שגיאה בתקשורת עם השירות' }]);
    } finally {
      setIsAiLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS'
    }).format(amount);
  };

  const renderDashboard = () => (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>דשבורד תקציבי</h1>
        <p>סקירה כללית של המצב הפיננסי שלך</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card income">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <h3>סך הכנסות</h3>
            <p className="stat-amount">{formatCurrency(summary.total_income || 0)}</p>
            <small>החודש: {formatCurrency(summary.current_month_income || 0)}</small>
          </div>
        </div>

        <div className="stat-card expense">
          <div className="stat-icon">💸</div>
          <div className="stat-content">
            <h3>סך הוצאות</h3>
            <p className="stat-amount">{formatCurrency(summary.total_expenses || 0)}</p>
            <small>החודש: {formatCurrency(summary.current_month_expenses || 0)}</small>
          </div>
        </div>

        <div className="stat-card balance">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>יתרה</h3>
            <p className="stat-amount">{formatCurrency(summary.total_balance || 0)}</p>
            <small>החודש: {formatCurrency(summary.current_month_balance || 0)}</small>
          </div>
        </div>

        <div className="stat-card transactions">
          <div className="stat-icon">📝</div>
          <div className="stat-content">
            <h3>עסקאות</h3>
            <p className="stat-amount">{summary.total_transactions || 0}</p>
            <small>סה״כ רשומות</small>
          </div>
        </div>
      </div>

      <div className="recent-transactions">
        <h2>עסקאות אחרונות</h2>
        <div className="transactions-list">
          {transactions.slice(0, 5).map(transaction => (
            <div key={transaction.id} className={`transaction-item ${transaction.type}`}>
              <div className="transaction-info">
                <span className="transaction-description">{transaction.description}</span>
                <span className="transaction-category">{transaction.category}</span>
              </div>
              <div className="transaction-details">
                <span className="transaction-amount">
                  {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                </span>
                <span className="transaction-date">{transaction.date}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="monthly-chart">
        <h2>מגמות חודשיות</h2>
        <div className="chart-container">
          {monthlyStats.slice(0, 6).map(stat => (
            <div key={stat.month} className="chart-bar">
              <div className="bar-container">
                <div className="bar income" style={{height: `${(stat.total_income / 20000) * 100}%`}}></div>
                <div className="bar expense" style={{height: `${(stat.total_expenses / 20000) * 100}%`}}></div>
              </div>
              <div className="bar-label">{stat.month}</div>
              <div className="bar-values">
                <small>הכנסות: {formatCurrency(stat.total_income)}</small>
                <small>הוצאות: {formatCurrency(stat.total_expenses)}</small>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTransactionForm = () => (
    <div className="transaction-form-container">
      <h2>הוסף עסקה חדשה</h2>
      <form onSubmit={handleSubmitTransaction} className="transaction-form">
        <div className="form-group">
          <label>סוג עסקה</label>
          <select 
            value={newTransaction.type} 
            onChange={(e) => setNewTransaction({...newTransaction, type: e.target.value})}
          >
            <option value="expense">הוצאה</option>
            <option value="income">הכנסה</option>
          </select>
        </div>

        <div className="form-group">
          <label>סכום</label>
          <input 
            type="number" 
            value={newTransaction.amount}
            onChange={(e) => setNewTransaction({...newTransaction, amount: e.target.value})}
            placeholder="0.00"
            step="0.01"
            required
          />
        </div>

        <div className="form-group">
          <label>קטגוריה</label>
          <select 
            value={newTransaction.category}
            onChange={(e) => setNewTransaction({...newTransaction, category: e.target.value})}
            required
          >
            <option value="">בחר קטגוריה</option>
            {categories
              .filter(cat => cat.type === newTransaction.type)
              .map(category => (
                <option key={category.id} value={category.name}>
                  {category.icon} {category.name}
                </option>
              ))}
          </select>
        </div>

        <div className="form-group">
          <label>תיאור</label>
          <input 
            type="text"
            value={newTransaction.description}
            onChange={(e) => setNewTransaction({...newTransaction, description: e.target.value})}
            placeholder="תיאור העסקה"
            required
          />
        </div>

        <div className="form-group">
          <label>תאריך</label>
          <input 
            type="date"
            value={newTransaction.date}
            onChange={(e) => setNewTransaction({...newTransaction, date: e.target.value})}
            required
          />
        </div>

        <button type="submit" className="submit-btn">הוסף עסקה</button>
      </form>
    </div>
  );

  const renderAiInsights = () => (
    <div className="ai-insights">
      <h2>יועץ פיננסי AI</h2>
      <div className="ai-chat-container">
        <div className="ai-messages">
          {aiMessages.length === 0 && (
            <div className="ai-welcome">
              <h3>שלום! אני היועץ הפיננסי שלך 🤖</h3>
              <p>אני יכול לעזור לך עם:</p>
              <ul>
                <li>ניתוח הרגלי הוצאה</li>
                <li>הצעות לחיסכון</li>
                <li>תכנון תקציב</li>
                <li>עצות השקעה</li>
              </ul>
              <p>שאל אותי כל שאלה על התקציב שלך!</p>
            </div>
          )}
          {aiMessages.map((msg, index) => (
            <div key={index} className={`ai-message ${msg.type}`}>
              <div className="message-content">
                {msg.message}
              </div>
            </div>
          ))}
          {isAiLoading && (
            <div className="ai-message ai">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
        </div>
        <form onSubmit={handleAiChat} className="ai-input-form">
          <input
            type="text"
            value={aiInput}
            onChange={(e) => setAiInput(e.target.value)}
            placeholder="שאל את היועץ שלך..."
            disabled={isAiLoading}
          />
          <button type="submit" disabled={isAiLoading}>
            {isAiLoading ? '🔄' : '📤'}
          </button>
        </form>
      </div>
    </div>
  );

  const renderHouseholdComparison = () => (
    <div className="household-comparison">
      <h2>השוואה למשקי בית דומים</h2>
      
      {householdComparison && (
        <div className="comparison-container">
          <div className="comparison-overview">
            <div className="comparison-card">
              <h3>המשק שלך</h3>
              <div className="comparison-stats">
                <div className="stat">
                  <span className="label">הכנסות חודשיות:</span>
                  <span className="value">{formatCurrency(householdComparison.user_data.income)}</span>
                </div>
                <div className="stat">
                  <span className="label">הוצאות חודשיות:</span>
                  <span className="value">{formatCurrency(householdComparison.user_data.expenses)}</span>
                </div>
                <div className="stat">
                  <span className="label">שיעור חיסכון:</span>
                  <span className="value">{householdComparison.user_data.savings_rate.toFixed(1)}%</span>
                </div>
              </div>
            </div>

            <div className="comparison-card">
              <h3>משק בית ממוצע</h3>
              <div className="comparison-stats">
                <div className="stat">
                  <span className="label">הכנסות חודשיות:</span>
                  <span className="value">{formatCurrency(householdComparison.average_household.income)}</span>
                </div>
                <div className="stat">
                  <span className="label">הוצאות חודשיות:</span>
                  <span className="value">{formatCurrency(householdComparison.average_household.expenses)}</span>
                </div>
                <div className="stat">
                  <span className="label">שיעור חיסכון:</span>
                  <span className="value">{householdComparison.average_household.savings_rate}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="category-comparison">
            <h3>השוואת הוצאות לפי קטגוריות</h3>
            <div className="category-grid">
              {Object.entries(householdComparison.category_comparison).map(([category, data]) => (
                <div key={category} className="category-comparison-item">
                  <h4>{category}</h4>
                  <div className="comparison-bars">
                    <div className="bar-row">
                      <span className="bar-label">אתה:</span>
                      <div className="bar-container">
                        <div 
                          className="bar user-bar" 
                          style={{width: `${(data.user / Math.max(data.user, data.average)) * 100}%`}}
                        ></div>
                      </div>
                      <span className="bar-value">{formatCurrency(data.user)}</span>
                    </div>
                    <div className="bar-row">
                      <span className="bar-label">ממוצע:</span>
                      <div className="bar-container">
                        <div 
                          className="bar average-bar" 
                          style={{width: `${(data.average / Math.max(data.user, data.average)) * 100}%`}}
                        ></div>
                      </div>
                      <span className="bar-value">{formatCurrency(data.average)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderTransactionsList = () => (
    <div className="transactions-list-container">
      <h2>כל העסקאות</h2>
      <div className="transactions-grid">
        {transactions.map(transaction => (
          <div key={transaction.id} className={`transaction-card ${transaction.type}`}>
            <div className="transaction-header">
              <span className="transaction-type-badge">{transaction.type === 'income' ? 'הכנסה' : 'הוצאה'}</span>
              <span className="transaction-date">{transaction.date}</span>
            </div>
            <div className="transaction-body">
              <h4>{transaction.description}</h4>
              <p className="transaction-category">{transaction.category}</p>
              <p className="transaction-amount">
                {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>💰 תקציב חכם</h1>
        </div>
        <div className="nav-links">
          <button 
            className={currentView === 'dashboard' ? 'active' : ''}
            onClick={() => setCurrentView('dashboard')}
          >
            📊 דשבורד
          </button>
          <button 
            className={currentView === 'add-transaction' ? 'active' : ''}
            onClick={() => setCurrentView('add-transaction')}
          >
            ➕ הוסף עסקה
          </button>
          <button 
            className={currentView === 'transactions' ? 'active' : ''}
            onClick={() => setCurrentView('transactions')}
          >
            📝 עסקאות
          </button>
          <button 
            className={currentView === 'ai-insights' ? 'active' : ''}
            onClick={() => setCurrentView('ai-insights')}
          >
            🤖 יועץ AI
          </button>
          <button 
            className={currentView === 'comparison' ? 'active' : ''}
            onClick={() => setCurrentView('comparison')}
          >
            📈 השוואה
          </button>
        </div>
      </nav>

      <main className="main-content">
        {currentView === 'dashboard' && renderDashboard()}
        {currentView === 'add-transaction' && renderTransactionForm()}
        {currentView === 'transactions' && renderTransactionsList()}
        {currentView === 'ai-insights' && renderAiInsights()}
        {currentView === 'comparison' && renderHouseholdComparison()}
      </main>
    </div>
  );
};

export default App;