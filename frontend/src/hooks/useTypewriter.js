import { useState, useEffect, useCallback } from 'react'

/**
 * Custom hook for typewriter text animation effect.
 *
 * Args:
 *     phrases: Array of strings to cycle through randomly
 *     typingSpeed: Milliseconds per character when typing (default: 60)
 *     deletingSpeed: Milliseconds per character when deleting (default: 30)
 *     pauseDuration: Milliseconds to pause after completing a phrase (default: 2500)
 *
 * Returns:
 *     string: Current text being displayed
 */
export function useTypewriter(
  phrases,
  typingSpeed = 60,
  deletingSpeed = 30,
  pauseDuration = 2500
) {
  const getRandomIndex = useCallback((currentIndex) => {
    if (phrases.length <= 1) return 0
    let newIndex
    do {
      newIndex = Math.floor(Math.random() * phrases.length)
    } while (newIndex === currentIndex)
    return newIndex
  }, [phrases.length])

  const [text, setText] = useState('')
  const [phraseIndex, setPhraseIndex] = useState(() => Math.floor(Math.random() * phrases.length))
  const [isDeleting, setIsDeleting] = useState(false)
  const [isPaused, setIsPaused] = useState(false)

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  useEffect(() => {
    if (prefersReducedMotion) {
      setText(phrases[Math.floor(Math.random() * phrases.length)])
      return
    }

    const currentPhrase = phrases[phraseIndex]

    if (isPaused) {
      const pauseTimer = setTimeout(() => {
        setIsPaused(false)
        setIsDeleting(true)
      }, pauseDuration)
      return () => clearTimeout(pauseTimer)
    }

    if (isDeleting) {
      if (text === '') {
        setIsDeleting(false)
        setPhraseIndex((prev) => getRandomIndex(prev))
      } else {
        const deleteTimer = setTimeout(() => {
          setText(text.slice(0, -1))
        }, deletingSpeed)
        return () => clearTimeout(deleteTimer)
      }
    } else {
      if (text === currentPhrase) {
        setIsPaused(true)
      } else {
        const typeTimer = setTimeout(() => {
          setText(currentPhrase.slice(0, text.length + 1))
        }, typingSpeed)
        return () => clearTimeout(typeTimer)
      }
    }
  }, [
    text,
    phraseIndex,
    isDeleting,
    isPaused,
    phrases,
    typingSpeed,
    deletingSpeed,
    pauseDuration,
    prefersReducedMotion,
    getRandomIndex,
  ])

  return text
}

export default useTypewriter
