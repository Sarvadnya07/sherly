import React, { useEffect, useRef } from 'react';
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
  const dialogRef = useRef<HTMLDivElement>(null);
  const approveBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Focus approve button on mount for explicit keyboard safety
    approveBtnRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onReject(actionId);
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, actionId, onReject, onClose]);

  if (!isOpen) return null;

  const riskColors = {
    low: 'text-status-info bg-status-info/10 border-status-info/20',
    medium: 'text-status-warning bg-status-warning/10 border-status-warning/20',
    high: 'text-status-danger bg-status-danger/10 border-status-danger/20',
    critical: 'text-status-danger bg-status-danger/20 border-status-danger/40',
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="approval-title"
        className="bg-card border border-border-medium rounded-lg max-w-md w-full p-5 shadow-elevated flex flex-col gap-4 select-none"
      >
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-md bg-status-danger/10 border border-status-danger/20 flex items-center justify-center text-status-danger shrink-0 mt-0.5">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 id="approval-title" className="text-sm font-semibold text-txt-primary">
              Operation Approval Required
            </h3>
            <p className="text-xs text-txt-muted mt-0.5">
              Sherly is requesting permission to perform an action on your workspace.
            </p>
          </div>
        </div>

        {/* Action Details Card */}
        <div className="bg-canvas border border-border-subtle rounded-md p-3.5 flex flex-col gap-2 text-xs font-mono">
          <div className="flex items-center justify-between">
            <span className="text-txt-muted font-sans">Action:</span>
            <span className="text-txt-primary font-bold">{actionName}</span>
          </div>

          {target && (
            <div className="flex items-center justify-between">
              <span className="text-txt-muted font-sans">Target:</span>
              <span className="text-txt-secondary truncate max-w-[220px]">{target}</span>
            </div>
          )}

          {reason && (
            <div className="flex flex-col gap-0.5 pt-1 border-t border-border-subtle">
              <span className="text-txt-muted font-sans">Reason:</span>
              <span className="text-txt-secondary font-sans text-xs leading-relaxed">{reason}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-1 border-t border-border-subtle">
            <span className="text-txt-muted font-sans">Risk Level:</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${riskColors[riskLevel]}`}>
              {riskLevel}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-txt-muted font-sans">Reversible:</span>
            <span className={isReversible ? 'text-status-success' : 'text-status-danger font-bold'}>
              {isReversible ? 'Yes' : 'No'}
            </span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-2.5 pt-1">
          <Button
            type="button"
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

          <button
            ref={approveBtnRef}
            type="button"
            onClick={() => {
              onApprove(actionId);
              onClose();
            }}
            className="inline-flex items-center justify-center font-medium transition duration-150 rounded-md bg-brand hover:bg-brand-hover text-white shadow-subtle text-xs px-3 py-1.5 gap-2 h-8 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand cursor-pointer"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Approve Action</span>
          </button>
        </div>
      </div>
    </div>
  );
};
