import { useState } from 'react'

export function useLocalStorage(key, initialValue = '') {
  const [value, setValue] = useState(() => localStorage.getItem(key) ?? initialValue)
  const save = (nextValue) => {
    setValue(nextValue)
    if (nextValue === '' || nextValue == null) localStorage.removeItem(key)
    else localStorage.setItem(key, nextValue)
  }
  return [value, save]
}
