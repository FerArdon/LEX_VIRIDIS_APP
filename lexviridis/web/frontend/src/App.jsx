import React, { useState, useEffect } from 'react'
import { Search, Library, Star, LayoutDashboard, Settings, ChevronRight, FileText, Info } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

function App() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState([])
    const [isLoading, setIsLoading] = useState(false)
    const [activeTab, setActiveTab] = useState('search')
    const [stats, setStats] = useState(null)

    useEffect(() => {
        fetchStats()
    }, [])

    const fetchStats = async () => {
        try {
            const res = await fetch('/api/stats')
            const data = await res.json()
            setStats(data)
        } catch (err) {
            console.error("Error fetching stats:", err)
        }
    }

    const handleSearch = async (e) => {
        const q = typeof e === 'string' ? e : query
        if (!q || q.length < 2) return

        setIsLoading(true)
        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`)
            const data = await res.json()
            setResults(data.results || [])
        } catch (err) {
            console.error("Search error:", err)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="flex h-screen overflow-hidden bg-slate-50">
            {/* Sidebar de navegación */}
            <nav className="w-20 lg:w-64 border-r bg-white flex flex-col h-full transition-all">
                <div className="p-6 flex items-center gap-3">
                    <div className="bg-green-700 p-2 rounded-lg">
                        <Library className="text-white" size={24} />
                    </div>
                    <span className="font-bold text-xl text-slate-800 hidden lg:block">LEX VIRIDIS</span>
                </div>

                <div className="flex-1 mt-6 px-4 space-y-2">
                    {[
                        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
                        { id: 'search', label: 'Buscador', icon: Search },
                        { id: 'favorites', label: 'Favoritos', icon: Star },
                        { id: 'library', label: 'Biblioteca', icon: Library },
                        { id: 'settings', label: 'Ajustes', icon: Settings },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${activeTab === item.id
                                    ? 'bg-green-700 text-white'
                                    : 'text-slate-500 hover:bg-slate-100'
                                }`}
                        >
                            <item.icon size={20} />
                            <span className="font-medium hidden lg:block">{item.label}</span>
                        </button>
                    ))}
                </div>

                <div className="p-4 border-t hidden lg:block">
                    <div className="bg-slate-50 p-4 rounded-xl border">
                        <p className="text-xs font-semibold text-slate-400 mb-2 uppercase">Sistema v2.0</p>
                        <p className="text-xs text-slate-500">Legislación Ambiental Honduras</p>
                    </div>
                </div>
            </nav>

            {/* Contenido Principal */}
            <main className="flex-1 overflow-y-auto">
                <header className="h-20 border-b bg-white flex items-center justify-between px-8 sticky top-0 z-10">
                    <h1 className="text-xl font-semibold text-slate-800 capitalize">{activeTab}</h1>
                    <div className="flex items-center gap-4">
                        <button className="p-2 text-slate-400 hover:text-green-700 transition-colors">
                            <Info size={20} />
                        </button>
                    </div>
                </header>

                <div className="p-8 max-w-6xl mx-auto">
                    {activeTab === 'search' && (
                        <div className="space-y-8 animate-in fade-in duration-500">
                            <div className="text-center space-y-4 py-8">
                                <h2 className="text-4xl font-bold text-slate-900">¿Qué buscas hoy?</h2>
                                <p className="text-slate-500 text-lg">Consulta leyes, decretos y artículos ambientales en segundos.</p>
                            </div>

                            <div className="max-w-2xl mx-auto">
                                <div className="relative group">
                                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-green-700 transition-colors" size={24} />
                                    <input
                                        type="text"
                                        placeholder="Busca por palabra clave (ej. licencia ambiental, forestal)..."
                                        className="w-full bg-white border-2 border-slate-200 rounded-2xl py-4 pl-14 pr-6 text-lg focus:outline-none focus:border-green-700 focus:ring-4 focus:ring-green-100 transition-all shadow-sm"
                                        value={query}
                                        onChange={(e) => setQuery(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                    />
                                </div>
                                <div className="flex flex-wrap gap-2 mt-4 justify-center">
                                    {['Licencia Ambiental', 'Delitos Forestales', 'Código Penal', 'Agua'].map(tag => (
                                        <button
                                            key={tag}
                                            onClick={() => { setQuery(tag); handleSearch(tag); }}
                                            className="px-4 py-1.5 bg-white border border-slate-200 rounded-full text-sm text-slate-600 hover:border-green-700 hover:text-green-700 transition-colors"
                                        >
                                            {tag}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-4 mt-12">
                                {isLoading ? (
                                    <div className="flex flex-col items-center py-20 gap-4">
                                        <div className="w-12 h-12 border-4 border-green-700 border-t-transparent rounded-full animate-spin"></div>
                                        <p className="text-slate-500 font-medium">Consultando registros...</p>
                                    </div>
                                ) : results.length > 0 ? (
                                    results.map((res, i) => (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.05 }}
                                            key={res.id}
                                            className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all flex gap-4 cursor-pointer group"
                                        >
                                            <div className="p-3 bg-green-50 text-green-700 rounded-xl h-fit">
                                                <FileText size={24} />
                                            </div>
                                            <div className="flex-1 space-y-1">
                                                <div className="flex items-center justify-between">
                                                    <h3 className="font-bold text-slate-900 group-hover:text-green-700 transition-colors">{res.file}</h3>
                                                    <div className="flex gap-1 text-amber-500">
                                                        {Array(5).fill(0).map((_, idx) => <span key={idx}>⭐</span>)}
                                                    </div>
                                                </div>
                                                <p className="text-slate-500 text-sm font-medium">Art. {res.id} • Página {res.page}</p>
                                                <p className="text-slate-600 mt-2 leading-relaxed" dangerouslySetInnerHTML={{ __html: res.context.replace(/\*\*(.*?)\*\*/g, '<mark class="bg-yellow-100 font-bold px-1 rounded">$1</mark>') }}></p>
                                            </div>
                                            <ChevronRight className="text-slate-300 self-center" />
                                        </motion.div>
                                    ))
                                ) : query && !isLoading && (
                                    <div className="text-center py-20 text-slate-400">
                                        <Search size={48} className="mx-auto mb-4 opacity-20" />
                                        <p>No encontramos resultados para tu búsqueda.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'dashboard' && stats && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-in fade-in duration-500">
                            {[
                                { label: 'Normas', value: stats.total_normas, color: 'text-blue-600', bg: 'bg-blue-50' },
                                { label: 'Artículos', value: stats.total_articulos, color: 'text-green-600', bg: 'bg-green-50' },
                                { label: 'Favoritos', value: stats.total_favoritos, color: 'text-amber-600', bg: 'bg-amber-50' },
                                { label: 'Búsquedas', value: stats.total_busquedas, color: 'text-indigo-600', bg: 'bg-indigo-50' },
                            ].map((stat, i) => (
                                <div key={i} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
                                    <div className={`p-4 ${stat.bg} ${stat.color} rounded-2xl`}>
                                        <LayoutDashboard size={24} />
                                    </div>
                                    <div>
                                        <p className="text-slate-500 text-sm">{stat.label}</p>
                                        <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                                    </div>
                                </div>
                            ))}

                            <div className="md:col-span-2 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm h-64 flex items-center justify-center text-slate-400 italic">
                                Gráfica de Actividad próximamente (React ChartJS)
                            </div>
                            <div className="md:col-span-2 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm h-64 flex items-center justify-center text-slate-400 italic">
                                Distribución por Tipo próximamente
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    )
}

export default App
