import React, { useState, useEffect } from 'react';

function App() {
  const [users, setUsers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showWelcome, setShowWelcome] = useState(true);

  // Mock data for demonstration
  const mockUsers = [
    { id: 1, name: 'John Doe', email: 'john@mycg.ai' },
    { id: 2, name: 'Jane Smith', email: 'jane@mycg.ai' },
    { id: 3, name: 'Alex Johnson', email: 'alex@mycg.ai' }
  ];

  const mockProducts = [
    { id: 1, name: 'AI Analytics Pro', price: '299.99' },
    { id: 2, name: 'Smart Dashboard', price: '199.99' },
    { id: 3, name: 'Data Insights Suite', price: '399.99' }
  ];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // In a real implementation, replace these with actual API calls:
        // const usersResponse = await fetch('/api/node/users');
        // const users = await usersResponse.json();
        // setUsers(users);
        
        // const productsResponse = await fetch('/api/python/products');
        // const products = await productsResponse.json();
        // setProducts(products);
        
        // For demo purposes, using mock data:
        setUsers(mockUsers);
        setProducts(mockProducts);
        
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(`Failed to fetch data: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };

    if (!showWelcome) {
      fetchData();
    }
  }, [showWelcome]);

  const handleGetStarted = () => {
    setShowWelcome(false);
  };

  // Welcome Page
  if (showWelcome) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          background: 'white',
          borderRadius: '20px',
          padding: '60px 40px',
          maxWidth: '600px',
          textAlign: 'center',
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          margin: '20px'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🚀</div>
          
          <h1 style={{ 
            fontSize: '2.5rem', 
            color: '#333', 
            marginBottom: '10px',
            fontWeight: 'bold'
          }}>
            Welcome to MyCG AI
          </h1>
          
          <p style={{ 
            fontSize: '1.2rem', 
            color: '#666', 
            marginBottom: '30px',
            lineHeight: '1.6'
          }}>
            Your intelligent microservices platform powered by cutting-edge AI technology
          </p>
          
          <div style={{ 
            background: '#f8f9fa', 
            borderRadius: '15px', 
            padding: '25px', 
            marginBottom: '30px',
            textAlign: 'left'
          }}>
            <h3 style={{ color: '#333', marginBottom: '15px', textAlign: 'center' }}>
              🎯 Platform Features
            </h3>
            <ul style={{ 
              listStyle: 'none', 
              padding: 0, 
              color: '#555',
              fontSize: '1rem'
            }}>
              <li style={{ marginBottom: '10px' }}>
                <span style={{ color: '#667eea', fontWeight: 'bold' }}>⚡</span> 
                High-performance microservices architecture
              </li>
              <li style={{ marginBottom: '10px' }}>
                <span style={{ color: '#667eea', fontWeight: 'bold' }}>🤖</span> 
                AI-powered data processing and analytics
              </li>
              <li style={{ marginBottom: '10px' }}>
                <span style={{ color: '#667eea', fontWeight: 'bold' }}>🔗</span> 
                Seamless integration between Node.js and Python services
              </li>
              <li style={{ marginBottom: '10px' }}>
                <span style={{ color: '#667eea', fontWeight: 'bold' }}>📊</span> 
                Real-time monitoring and health checks
              </li>
              <li>
                <span style={{ color: '#667eea', fontWeight: 'bold' }}>🛡️</span> 
                Enterprise-grade security and scalability
              </li>
            </ul>
          </div>
          
          <button 
            onClick={handleGetStarted}
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              padding: '15px 40px',
              fontSize: '1.1rem',
              borderRadius: '50px',
              cursor: 'pointer',
              fontWeight: 'bold',
              boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)',
              transition: 'all 0.3s ease',
              transform: 'translateY(0)'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 15px 40px rgba(102, 126, 234, 0.6)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 10px 30px rgba(102, 126, 234, 0.4)';
            }}
          >
            🚀 Get Started
          </button>
          
          <p style={{ 
            marginTop: '25px', 
            fontSize: '0.9rem', 
            color: '#999' 
          }}>
            Ready to explore your microservices dashboard?
          </p>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div style={{ 
        fontFamily: 'Arial, sans-serif',
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '20px'
      }}>
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          background: '#f8f9fa',
          borderRadius: '15px',
          margin: '20px 0'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🔄</div>
          <h2 style={{ color: '#333', marginBottom: '15px' }}>Loading MyCG AI Services...</h2>
          <p style={{ color: '#666' }}>Please wait while we connect to all microservices.</p>
          <div style={{
            width: '200px',
            height: '4px',
            background: '#eee',
            borderRadius: '2px',
            margin: '20px auto',
            overflow: 'hidden'
          }}>
            <div style={{
              width: '100%',
              height: '100%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              animation: 'pulse 2s ease-in-out infinite'
            }}></div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ 
        fontFamily: 'Arial, sans-serif',
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '20px'
      }}>
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          background: '#ffe6e6',
          borderRadius: '15px',
          margin: '20px 0',
          border: '1px solid #ffcccc'
        }}>
          <h2 style={{ color: '#d00', marginBottom: '15px' }}>❌ Error</h2>
          <p style={{ color: '#800' }}>{error}</p>
          <button 
            onClick={() => setShowWelcome(true)}
            style={{
              background: '#d00',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '25px',
              cursor: 'pointer',
              marginTop: '15px'
            }}
          >
            Return to Welcome
          </button>
        </div>
      </div>
    );
  }

  // Main Dashboard
  return (
    <div style={{ 
      fontFamily: 'Arial, sans-serif',
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '20px'
    }}>
      <div style={{
        textAlign: 'center',
        marginBottom: '40px',
        padding: '30px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '15px',
        color: 'white'
      }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '10px' }}>🚀 MyCG AI Dashboard</h1>
        <p style={{ fontSize: '1.1rem', opacity: '0.9' }}>
          React Frontend • Node.js Backend • Python Backend • PostgreSQL Databases
        </p>
        <button 
          onClick={() => setShowWelcome(true)}
          style={{
            background: 'rgba(255,255,255,0.2)',
            color: 'white',
            border: '1px solid rgba(255,255,255,0.3)',
            padding: '8px 20px',
            borderRadius: '25px',
            cursor: 'pointer',
            marginTop: '15px',
            fontSize: '0.9rem'
          }}
        >
          ← Back to Welcome
        </button>
      </div>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '30px',
        marginBottom: '40px'
      }}>
        <div style={{
          background: 'white',
          borderRadius: '15px',
          padding: '30px',
          boxShadow: '0 5px 20px rgba(0,0,0,0.1)',
          border: '1px solid #eee'
        }}>
          <h2 style={{ color: '#333', marginBottom: '15px' }}>👥 Users Service</h2>
          <p style={{ color: '#666', marginBottom: '20px' }}>
            <strong>Backend:</strong> Node.js + Express + PostgreSQL
          </p>
          {users.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {users.map(user => (
                <li key={user.id} style={{
                  background: '#f8f9fa',
                  padding: '15px',
                  marginBottom: '10px',
                  borderRadius: '10px',
                  borderLeft: '4px solid #667eea'
                }}>
                  <strong style={{ color: '#333' }}>{user.name}</strong><br />
                  <small style={{ color: '#666' }}>{user.email}</small>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: '#999', fontStyle: 'italic' }}>No users found</p>
          )}
        </div>

        <div style={{
          background: 'white',
          borderRadius: '15px',
          padding: '30px',
          boxShadow: '0 5px 20px rgba(0,0,0,0.1)',
          border: '1px solid #eee'
        }}>
          <h2 style={{ color: '#333', marginBottom: '15px' }}>🛍️ Products Service</h2>
          <p style={{ color: '#666', marginBottom: '20px' }}>
            <strong>Backend:</strong> Python + Flask + PostgreSQL
          </p>
          {products.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {products.map(product => (
                <li key={product.id} style={{
                  background: '#f8f9fa',
                  padding: '15px',
                  marginBottom: '10px',
                  borderRadius: '10px',
                  borderLeft: '4px solid #764ba2'
                }}>
                  <strong style={{ color: '#333' }}>{product.name}</strong><br />
                  <small style={{ color: '#666' }}>${product.price}</small>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: '#999', fontStyle: 'italic' }}>No products found</p>
          )}
        </div>
      </div>

      <div style={{
        background: 'white',
        borderRadius: '15px',
        padding: '30px',
        boxShadow: '0 5px 20px rgba(0,0,0,0.1)',
        border: '1px solid #eee',
        textAlign: 'center'
      }}>
        <h3 style={{ color: '#333', marginBottom: '20px' }}>🔗 API Health Checks</h3>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          gap: '20px',
          flexWrap: 'wrap'
        }}>
          <a 
            href="/api/node/health" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{
              background: '#667eea',
              color: 'white',
              padding: '12px 24px',
              borderRadius: '25px',
              textDecoration: 'none',
              fontWeight: 'bold',
              transition: 'background 0.3s ease'
            }}
          >
            Node.js Health
          </a>
          <a 
            href="/api/python/health" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{
              background: '#764ba2',
              color: 'white',
              padding: '12px 24px',
              borderRadius: '25px',
              textDecoration: 'none',
              fontWeight: 'bold',
              transition: 'background 0.3s ease'
            }}
          >
            Python Health
          </a>
        </div>
        <p style={{ 
          marginTop: '20px', 
          fontSize: '14px', 
          color: '#666',
          lineHeight: '1.5'
        }}>
          <strong>Architecture:</strong> Nginx Reverse Proxy → React (Port 3001) + Node.js (Port 5001) + Python (Port 8001)
        </p>
      </div>
    </div>
  );
}

export default App;