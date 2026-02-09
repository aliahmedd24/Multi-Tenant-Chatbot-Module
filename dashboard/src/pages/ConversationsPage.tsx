import { MessageSquare } from 'lucide-react';

export function ConversationsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-900">Conversations</h1>
                <p className="text-slate-500">View and manage customer conversations</p>
            </div>

            {/* Placeholder for conversations list */}
            <div className="bg-white rounded-2xl p-12 shadow-sm border border-slate-100 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-violet-100 mb-4">
                    <MessageSquare className="text-violet-600" size={32} />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    Conversations will appear here
                </h3>
                <p className="text-slate-500 max-w-md mx-auto">
                    When customers message your channels, their conversations will be listed here.
                    Configure a channel first to start receiving messages.
                </p>
            </div>
        </div>
    );
}
