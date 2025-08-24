import React, { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in (for demo purposes, we'll use localStorage)
    const token = localStorage.getItem('authToken')
    const userData = localStorage.getItem('userData')
    
    if (token && userData) {
      setIsAuthenticated(true)
      setUser(JSON.parse(userData))
    }
    setLoading(false)
  }, [])

  const login = (userData) => {
    // Simulate API call
    const mockUser = {
      id: 1,
      name: userData.email.split('@')[0],
      email: userData.email,
      role: 'Employee',
      department: 'Engineering'
    }
    
    localStorage.setItem('authToken', 'mock-token-123')
    localStorage.setItem('userData', JSON.stringify(mockUser))
    setIsAuthenticated(true)
    setUser(mockUser)
  }

  const register = (userData) => {
    // Simulate API call
    const mockUser = {
      id: Date.now(),
      name: userData.name,
      email: userData.email,
      role: 'Employee',
      department: 'Engineering'
    }
    
    localStorage.setItem('authToken', 'mock-token-123')
    localStorage.setItem('userData', JSON.stringify(mockUser))
    setIsAuthenticated(true)
    setUser(mockUser)
  }

  const logout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('userData')
    setIsAuthenticated(false)
    setUser(null)
  }

  const value = {
    isAuthenticated,
    user,
    loading,
    login,
    register,
    logout
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
