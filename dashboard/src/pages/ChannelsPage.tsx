import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Radio, MessageCircle } from 'lucide-react';
import { useState } from 'react';
import { channelsApi } from '../api';
import type { Channel } from '../types';

export function ChannelsPage() {
    const queryClient = useQueryClient();
    const [showCreateModal, setShowCreateModal] = useState(false);

    const { data, isLoading } = useQuery({
        queryKey: ['channels'],
        queryFn: channelsApi.list,
    });

    const deleteMutation = useMutation({
        mutationFn: channelsApi.delete,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['channels'] }),
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Channels</h1>
                    <p className="text-slate-500">Manage your WhatsApp and Instagram integrations</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors"
                >
                    <Plus size={20} />
                    Add Channel
                </button>
            </div>

            {/* Channels Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {data?.channels.map((channel) => (
                    <ChannelCard
                        key={channel.id}
                        channel={channel}
                        onDelete={() => {
                            if (confirm('Delete this channel? This cannot be undone.')) {
                                deleteMutation.mutate(channel.id);
                            }
                        }}
                    />
                ))}
                {(data?.channels.length ?? 0) === 0 && (
                    <div className="col-span-full py-12 text-center text-slate-500">
                        No channels configured. Add your first channel to get started.
                    </div>
                )}
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <CreateChannelModal onClose={() => setShowCreateModal(false)} />
            )}
        </div>
    );
}

function ChannelCard({
    channel,
    onDelete
}: {
    channel: Channel;
    onDelete: () => void;
}) {
    const isWhatsApp = channel.channel_type === 'whatsapp';

    return (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-xl ${isWhatsApp ? 'bg-green-100' : 'bg-pink-100'}`}>
                        {isWhatsApp ? (
                            <MessageCircle className="text-green-600" size={24} />
                        ) : (
                            <Radio className="text-pink-600" size={24} />
                        )}
                    </div>
                    <div>
                        <h3 className="font-semibold text-slate-900">{channel.name}</h3>
                        <p className="text-sm text-slate-500 capitalize">{channel.channel_type}</p>
                    </div>
                </div>
                <button
                    onClick={onDelete}
                    className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >
                    <Trash2 size={18} />
                </button>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100 space-y-2">
                <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Status</span>
                    <span className={`font-medium ${channel.is_active ? 'text-emerald-600' : 'text-slate-400'}`}>
                        {channel.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
                <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Webhook Secret</span>
                    <span className={`font-medium ${channel.has_webhook_secret ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {channel.has_webhook_secret ? 'Configured' : 'Not Set'}
                    </span>
                </div>
                {channel.last_webhook_at && (
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Last Webhook</span>
                        <span className="text-slate-600">
                            {new Date(channel.last_webhook_at).toLocaleDateString()}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}

function CreateChannelModal({ onClose }: { onClose: () => void }) {
    const queryClient = useQueryClient();
    const [formData, setFormData] = useState({
        name: '',
        channel_type: 'whatsapp' as 'whatsapp' | 'instagram',
        phone_number_id: '',
        instagram_page_id: '',
        access_token: '',
        webhook_secret: '',
    });

    const createMutation = useMutation({
        mutationFn: channelsApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
            onClose();
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        createMutation.mutate(formData);
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
                <h2 className="text-xl font-bold text-slate-900 mb-4">Add Channel</h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Type</label>
                        <select
                            value={formData.channel_type}
                            onChange={(e) => setFormData({ ...formData, channel_type: e.target.value as 'whatsapp' | 'instagram' })}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                        >
                            <option value="whatsapp">WhatsApp</option>
                            <option value="instagram">Instagram</option>
                        </select>
                    </div>

                    {formData.channel_type === 'whatsapp' ? (
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number ID</label>
                            <input
                                type="text"
                                value={formData.phone_number_id}
                                onChange={(e) => setFormData({ ...formData, phone_number_id: e.target.value })}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                                placeholder="From Meta Developer Console"
                            />
                        </div>
                    ) : (
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Instagram Page ID</label>
                            <input
                                type="text"
                                value={formData.instagram_page_id}
                                onChange={(e) => setFormData({ ...formData, instagram_page_id: e.target.value })}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                                placeholder="From Meta Developer Console"
                            />
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Access Token</label>
                        <input
                            type="password"
                            value={formData.access_token}
                            onChange={(e) => setFormData({ ...formData, access_token: e.target.value })}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                            placeholder="Platform API token"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Webhook Secret</label>
                        <input
                            type="password"
                            value={formData.webhook_secret}
                            onChange={(e) => setFormData({ ...formData, webhook_secret: e.target.value })}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                            placeholder="For signature verification"
                        />
                    </div>

                    <div className="flex gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={createMutation.isPending}
                            className="flex-1 px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors disabled:opacity-50"
                        >
                            {createMutation.isPending ? 'Creating...' : 'Create'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
