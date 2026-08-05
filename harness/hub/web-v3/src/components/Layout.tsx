import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { t } from '../lib/i18n'

export default function Layout() { const [sidebarCollapsed, setSidebarCollapsed] = useState(() => localStorage.getItem('hub-v3-sidebar-collapsed') === 'true'); const [drawerOpen, setDrawerOpen] = useState(false); useEffect(() => { localStorage.setItem('hub-v3-sidebar-collapsed', String(sidebarCollapsed)) }, [sidebarCollapsed]); return <div className={`app ${sidebarCollapsed ? 'sidebar-collapsed' : ''} ${drawerOpen ? 'sidebar-drawer-open' : ''}`}><Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(value => !value)} /><main className="main"><Topbar onOpenNavigation={() => setDrawerOpen(true)} /><section className="content"><Outlet /></section></main><button type="button" className="app-drawer-scrim" aria-label={t('common.close')} onClick={() => setDrawerOpen(false)} /></div> }
