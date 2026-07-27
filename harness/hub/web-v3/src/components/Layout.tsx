import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function Layout() { return <div className="app"><Sidebar /><main className="main"><Topbar /><section className="content"><Outlet /></section></main></div> }
