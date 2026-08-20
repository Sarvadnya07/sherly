import React from 'react';
import { Check, X, ShieldAlert } from 'lucide-react';
import { Button } from './Button';

export interface ApprovalDialogProps {
  isOpen: boolean;
  actionId: string;
  actionName: string;
  target?: string;
  reason?: string;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  isReversible?: boolean;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onClose: () => void;
}

export const ApprovalDialog: React.FC<ApprovalDialogProps> = ({
  isOpen,
  actionId,
  actionName,
  target,
  reason,
  riskLevel = 'medium',
  isReversible = false,
  onApprove,
  onReject,
  onClose,
}) => {
  if (!isOpen) return null;

  const riskColors = {
    low: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
    medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    high: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    critical: 'text-rose-500 bg-rose-600/15 border-rose-600/30',
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="approval-title"
        className="bg-card border border-white/[0.12] rounded-xl max-w-md w-full p-5 shadow-elevated flex flex-col gap-4"
      >
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-status-danger/15 border border-status-danger/30 flex items-center justify-center text-rose-400 shrink-0 mt-0.5">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <h3 id="approval-title" className="text-sm font-bold text-gray-100">
              Operation Approval Required
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Sherly is requesting permission to perform an action on your workspace.
            </p>
          </div>
        </div>

        {/* Action Details Card */}
        <div className="bg-canvas border border-white/[0.08] rounded-lg p-3.5 flex flex-col gap-2 text-xs font-mono">
          <div className="flex items-center justify-between">
            <span className="text-gray-500 font-sans">Action:</span>
            <span className="text-purple-300 font-bold">{actionName}</span>
          </div>

          {target && (
            <div className="flex items-center justify-between">
              <span className="text-gray-500 font-sans">Target:</span>
              <span className="text-gray-200 truncate max-w-[220px]">{target}</span>
            </div>
          )}

          {reason && (
            <div className="flex flex-col gap-0.5 pt-1 border-t border-white/[0.04]">
              <span className="text-gray-500 font-sans">Reason:</span>
              <span className="text-gray-300 font-sans text-[11px] leading-relaxed">{reason}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-1 border-t border-white/[0.04]">
            <span className="text-gray-500 font-sans">Risk Level:</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${riskColors[riskLevel]}`}>
              {riskLevel}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-gray-500 font-sans">Reversible:</span>
            <span className={isReversible ? 'text-emerald-400' : 'text-rose-400 font-bold'}>
              {isReversible ? 'Yes' : 'No'}
            </span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-2.5 pt-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              onReject(actionId);
              onClose();
            }}
            icon={<X className="w-3.5 h-3.5" />}
          >
            Reject (Esc)
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              onApprove(actionId);
              onClose();
            }}
            icon={<Check className="w-3.5 h-3.5" />}
          >
            Approve Action
          </Button>
        </div>
      </div>
    </div>
  );
};
