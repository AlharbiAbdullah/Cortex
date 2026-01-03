import React from 'react'
import { FiSun, FiMoon } from 'react-icons/fi'
import { useTheme } from '../context/ThemeContext'

function ThemeToggle() {
  const { isDark, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="fixed top-4 right-4 z-50 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-110"
      style={{
        background: 'var(--bg-tertiary)',
        border: '1px solid var(--border-color)',
        color: 'var(--text-primary)',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      }}
      onMouseEnter={(e) => e.currentTarget.style.background = 'var(--card-hover)'}
      onMouseLeave={(e) => e.currentTarget.style.background = 'var(--bg-tertiary)'}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? (
        <FiSun className="w-5 h-5" style={{ color: 'var(--yellow)' }} />
      ) : (
        <FiMoon className="w-5 h-5" style={{ color: 'var(--purple)' }} />
      )}
    </button>
  )
}

export default ThemeToggle
