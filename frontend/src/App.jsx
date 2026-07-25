import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './layouts/AdminLayout'
import PublicLayout from './layouts/PublicLayout'
import BookingPage from './pages/BookingPage'
import ChatPage from './pages/ChatPage'
import LandingPage from './pages/LandingPage'
import MyAppointmentsPage from './pages/MyAppointmentsPage'
import MessagesPage from './pages/MessagesPage'
import ScheduleRequestPage from './pages/ScheduleRequestPage'
import SuperadminSettingsPage from './pages/SuperadminSettingsPage'
import AdminAppointments from './pages/admin/AdminAppointments'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminRequests from './pages/admin/AdminRequests'
import AdminSchedule from './pages/admin/AdminSchedule'
import AdminServices from './pages/admin/AdminServices'
import AdminMessages from './pages/admin/AdminMessages'

export default function App() {
  return <BrowserRouter><Routes>
    <Route element={<PublicLayout />}>
      <Route index element={<LandingPage />} />
      <Route path="companies/:companyId/book" element={<BookingPage />} />
      <Route path="companies/:companyId/appointments" element={<MyAppointmentsPage />} />
      <Route path="companies/:companyId/chat" element={<ChatPage />} />
      <Route path="companies/:companyId/messages" element={<MessagesPage />} />
      <Route path="companies/:companyId/schedule-request" element={<ScheduleRequestPage />} />
    </Route>
    <Route path="admin/companies/:companyId" element={<AdminLayout />}>
      <Route index element={<AdminDashboard />} />
      <Route path="services" element={<AdminServices />} />
      <Route path="schedule" element={<AdminSchedule />} />
      <Route path="appointments" element={<AdminAppointments />} />
      <Route path="requests" element={<AdminRequests />} />
      <Route path="messages" element={<AdminMessages />} />
    </Route>
    {import.meta.env.VITE_ENABLE_SUPERADMIN === 'true' && <Route path="superadmin/settings" element={<SuperadminSettingsPage />} />}
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></BrowserRouter>
}
