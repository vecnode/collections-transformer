'use client'

import { 
    Sidebar,
    Menu,
    SubMenu,
    MenuItem
  } from "react-pro-sidebar";
import Link from 'next/link'
import Image from 'next/image'
import { useAuth } from "@/contexts/AuthContext";
import logo from '../../public/ual-logo.png'
import { useState } from "react";


const SideBar = () => {

    const { user, logout } = useAuth();

    const [collapsed, setCollapsed] = useState(false)

    return (
        <div className="sidebar-container flex">
            <Sidebar collapsed={collapsed}>
                <div className="sidebar-inner">
                    <div className="sidebar-header">
                        {!collapsed && <h4>Collections Transformer</h4>}
                        <button
                            type="button"
                            className="sidebar-collapse-btn"
                            onClick={() => setCollapsed((prev) => !prev)}
                            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                        >
                            <span className="material-symbols-outlined">
                                {collapsed ? 'chevron_right' : 'chevron_left'}
                            </span>
                        </button>
                    </div>
                    
                    <div className="sidebar-top">
                        <Menu>
                            
                            <MenuItem icon={<span className='material-symbols-outlined'>home</span>} component={<Link href="/" />}> Home </MenuItem>

                            <MenuItem icon={<span className='material-symbols-outlined'>hub</span>} component={<Link href="/workspace" />}> Workspace </MenuItem>
                            
                            <MenuItem icon={<span className='material-symbols-outlined'>psychology</span>} component={<Link href="/newagent" />}> New Agent </MenuItem>
                            
                            
                            <MenuItem icon={<span className='material-symbols-outlined'>upload</span>} component={<Link href="/dataset" />}> Dataset </MenuItem>

                            <MenuItem icon={<span className='material-symbols-outlined'>pattern</span>} component={<Link href="/tasks" />}> Tasks </MenuItem>
                            
                            <hr></hr>
                        </Menu>
                    </div>
                    
                    <div className="sidebar-bottom">   
                        <Menu>
                            <hr></hr>
                            <MenuItem icon={<span className='material-symbols-outlined'>account_circle</span>} component={<Link href="/user" />}> Profile </MenuItem>
                            <MenuItem icon={<span className='material-symbols-outlined'>settings</span>} component={<Link href="/settings" />}> Settings </MenuItem>
                            {user ? (
                                <MenuItem 
                                    icon={<span className='material-symbols-outlined'>logout</span>} 
                                    onClick={async () => {
                                        await logout();
                                        window.location.href = '/login';
                                    }}
                                > 
                                    Logout ({user.username || user.name}) 
                                </MenuItem> 
                            )
                            : (
                                <MenuItem icon={<span className='material-symbols-outlined'>login</span>} component={<Link href="/login" />}> Login </MenuItem> 
                            )}
                        </Menu>
                        <div style={{ display: "flex", justifyContent: "center" }}>
                            <Image 
                                src={logo}
                                width={collapsed ? 50 : 150}
                                alt="University Arts London Logo"
                            />
                        </div>
                    </div>
                </div>
            </Sidebar>
        </div>
    )
}

export default SideBar

