import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Dashboard = ({ token, user, onOpenItinerary }) => {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('active');

  const authHeaders = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);

  const fetchItems = async () => {
    if (!token) {
      navigate('/auth');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`${API_URL}/api/users/itineraries`, {
        headers: authHeaders,
      });
      setItems(response.data.items || []);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load itineraries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [token]);

  const splitItems = useMemo(() => {
    const now = new Date();
    const active = [];
    const previous = [];

    items.forEach((item) => {
      const endDate = item.endDate ? new Date(item.endDate) : null;
      const isPreviousByDate = endDate ? endDate < now : false;
      const isPrevious = item.status === 'previous' || isPreviousByDate;
      if (isPrevious) previous.push(item);
      else active.push(item);
    });

    return { active, previous };
  }, [items]);

  const markStatus = async (id, status) => {
    try {
      await axios.patch(
        `${API_URL}/api/users/itineraries/${id}/status`,
        { status },
        { headers: { ...authHeaders, 'Content-Type': 'application/json' } }
      );
      await fetchItems();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not update itinerary status');
    }
  };

  const removeItem = async (id) => {
    try {
      await axios.delete(`${API_URL}/api/users/itineraries/${id}`, {
        headers: authHeaders,
      });
      await fetchItems();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not delete itinerary');
    }
  };

  const renderCard = (item) => (
    <div key={item.id} className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
      <p className="text-xs uppercase text-slate-500">{item.destination || 'Destination'}</p>
      <h3 className="text-lg font-bold text-slate-900 mt-1">{item.title}</h3>
      <p className="text-sm text-slate-600 mt-1">
        {item.startDate || '-'} to {item.endDate || '-'}
      </p>

      <div className="flex flex-wrap gap-2 mt-4">
        <button
          onClick={() => {
            onOpenItinerary(item.itinerary);
            navigate('/');
          }}
          className="px-3 py-1.5 rounded-lg bg-sky-600 text-white text-sm font-medium"
        >
          Open
        </button>

        {activeTab === 'active' ? (
          <button
            onClick={() => markStatus(item.id, 'previous')}
            className="px-3 py-1.5 rounded-lg bg-amber-100 text-amber-800 text-sm font-medium"
          >
            Mark Previous
          </button>
        ) : (
          <button
            onClick={() => markStatus(item.id, 'active')}
            className="px-3 py-1.5 rounded-lg bg-emerald-100 text-emerald-800 text-sm font-medium"
          >
            Mark Active
          </button>
        )}

        <button
          onClick={() => removeItem(item.id)}
          className="px-3 py-1.5 rounded-lg bg-red-100 text-red-700 text-sm font-medium"
        >
          Delete
        </button>
      </div>
    </div>
  );

  const visibleItems = activeTab === 'active' ? splitItems.active : splitItems.previous;

  return (
    <div className="travel-page-shell min-h-screen px-4 pt-32 pb-16">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-black text-slate-900">{user?.name ? `${user.name}'s Dashboard` : 'Itinerary Dashboard'}</h1>
        <p className="text-slate-600 mt-1">Manage and revisit your saved trips anytime.</p>

        <div className="mt-6 inline-flex rounded-xl border border-slate-200 bg-white p-1">
          <button
            onClick={() => setActiveTab('active')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeTab === 'active' ? 'bg-slate-900 text-white' : 'text-slate-700'
            }`}
          >
            Active Itineraries ({splitItems.active.length})
          </button>
          <button
            onClick={() => setActiveTab('previous')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeTab === 'previous' ? 'bg-slate-900 text-white' : 'text-slate-700'
            }`}
          >
            Previous Itineraries ({splitItems.previous.length})
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-red-700">{error}</p>}

        {loading ? (
          <p className="mt-8 text-slate-600">Loading itineraries...</p>
        ) : visibleItems.length === 0 ? (
          <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-600">
            No itineraries in this tab yet.
          </div>
        ) : (
          <div className="mt-8 grid md:grid-cols-2 gap-4">{visibleItems.map(renderCard)}</div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
