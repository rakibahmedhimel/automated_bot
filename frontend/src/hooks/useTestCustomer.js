import { useEffect, useState } from 'react'

export const TEST_CUSTOMER_KEY = 'slotely_test_customer'
const PROFILE_EVENT = 'slotely-profile-changed'

function createExternalUserId() {
  const id = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`
  return `test-user-${id}`
}

function readProfile() {
  try {
    const saved = JSON.parse(localStorage.getItem(TEST_CUSTOMER_KEY))
    if (saved && typeof saved === 'object') {
      return {
        external_user_id: saved.external_user_id || createExternalUserId(),
        customer_name: saved.customer_name || '',
        customer_email: saved.customer_email || '',
        customer_phone: saved.customer_phone || '',
      }
    }
  } catch {
    localStorage.removeItem(TEST_CUSTOMER_KEY)
  }

  return {
    external_user_id: localStorage.getItem('slotely_external_user_id') || createExternalUserId(),
    customer_name: '',
    customer_email: '',
    customer_phone: '',
  }
}

function persistProfile(profile) {
  localStorage.setItem(TEST_CUSTOMER_KEY, JSON.stringify(profile))
  localStorage.setItem('slotely_external_user_id', profile.external_user_id)
  window.dispatchEvent(new CustomEvent(PROFILE_EVENT, { detail: profile }))
}

export function useTestCustomer() {
  const [profile, setProfile] = useState(() => {
    const initial = readProfile()
    persistProfile(initial)
    return initial
  })

  useEffect(() => {
    const syncProfile = (event) => setProfile(event.detail || readProfile())
    window.addEventListener(PROFILE_EVENT, syncProfile)
    return () => window.removeEventListener(PROFILE_EVENT, syncProfile)
  }, [])

  const saveProfile = (nextProfile) => {
    const normalized = {
      external_user_id: nextProfile.external_user_id.trim() || createExternalUserId(),
      customer_name: nextProfile.customer_name.trim(),
      customer_email: nextProfile.customer_email.trim(),
      customer_phone: nextProfile.customer_phone.trim(),
    }
    persistProfile(normalized)
    setProfile(normalized)
  }

  return [profile, saveProfile]
}
