import os

# Create static directory if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

# Create the visualizer.js file
with open('static/visualizer.js', 'w') as f:
    f.write('''
// Simple React component builder
const e = React.createElement;

function GameVisualizer() {
    const [stats, setStats] = React.useState(null);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                setStats(data);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return e('div', { className: 'p-4 text-center' }, 'Loading...');
    }

    const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } = Recharts;

    return e('div', { className: 'max-w-6xl mx-auto p-4 space-y-4' },
        e('div', { className: 'bg-white shadow rounded-lg p-4' },
            e('h1', { className: 'text-2xl font-bold mb-4' }, 'Push Battle Performance Analysis'),
            e('div', { className: 'grid grid-cols-1 md:grid-cols-2 gap-4' },
                e('div', { className: 'bg-gray-50 p-4 rounded-lg' },
                    e('h2', { className: 'text-xl font-semibold mb-2' }, 'Win Rate Distribution'),
                    e(BarChart, { width: 400, height: 300, data: stats.matchupStats },
                        e(CartesianGrid, { strokeDasharray: '3 3' }),
                        e(XAxis, { dataKey: 'name', angle: -45, textAnchor: 'end', height: 100 }),
                        e(YAxis),
                        e(Tooltip),
                        e(Legend),
                        e(Bar, { dataKey: 'wins', fill: '#4CAF50' }),
                        e(Bar, { dataKey: 'losses', fill: '#f44336' }),
                        e(Bar, { dataKey: 'draws', fill: '#9e9e9e' })
                    )
                ),
                e('div', { className: 'bg-gray-50 p-4 rounded-lg' },
                    e('h2', { className: 'text-xl font-semibold mb-2' }, 'Move Quality by Game Phase'),
                    e(BarChart, { width: 400, height: 300, data: stats.moveStats },
                        e(CartesianGrid, { strokeDasharray: '3 3' }),
                        e(XAxis, { dataKey: 'name' }),
                        e(YAxis),
                        e(Tooltip),
                        e(Legend),
                        e(Bar, { dataKey: 'validMoves', fill: '#4CAF50' }),
                        e(Bar, { dataKey: 'timeouts', fill: '#f44336' }),
                        e(Bar, { dataKey: 'invalid', fill: '#ff9800' })
                    )
                )
            )
        )
    );
}

// Render the app
ReactDOM.render(
    e(GameVisualizer),
    document.getElementById('root')
);
''')

print("Visualizer built successfully!")