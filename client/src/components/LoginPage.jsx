import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const [user, setUser] = useState('')
  const [pass, setPass] = useState('')
  const [err, setErr] = useState('')
  const nav = useNavigate()

  const handleLogin = e => {
    e.preventDefault()

    const match = user.match(/^user(\d+)$/)
    if (match) {
      const id = match[1]
      if (pass === `pass${id}`) {
        localStorage.setItem('userId', id)
        nav('/recs')
        return
      }
    }

    setErr('Invalid credentials')
  }

  return (
    <div className="max-w-sm mx-auto p-6 mt-20 bg-white rounded shadow">
      <h2 className="text-2xl mb-4">Login</h2>
      {err && <p className="text-red-500 mb-2">{err}</p>}
      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className="block">Username</label>
          <input
            className="w-full border px-2 py-1"
            value={user}
            onChange={e => setUser(e.target.value)}
            placeholder="e.g. user3"
          />
        </div>
        <div>
          <label className="block">Password</label>
          <input
            type="password"
            className="w-full border px-2 py-1"
            value={pass}
            onChange={e => setPass(e.target.value)}
            placeholder="e.g. pass3"
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded"
        >
          Login
        </button>
      </form>
    </div>
  )
}
