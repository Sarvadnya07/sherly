import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  size?: 'sm' | 'md';
  pulse?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'sm',
  pulse = false,
  className = '',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center gap-1 font-mono font-medium rounded select-none';

  const variants = {
    brand: 'bg-brand-surface text-purple-300 border border-brand-border',
    success: 'bg-status-success/10 text-emerald-400 border border-status-success/20',
    warning: 'bg-status-warning/10 text-amber-400 border border-status-warning/20',
    danger: 'bg-status-danger/10 text-rose-400 border border-status-danger/20',
    info: 'bg-status-info/10 text-sky-400 border border-status-info/20',
    neutral: 'bg-white/[0.05] text-gray-300 border border-white/[0.08]',
  };

  const sizes = {
    sm: 'text-[10px] px-1.5 py-0.5 leading-none',
    md: 'text-[11px] px-2 py-0.5 leading-tight',
  };

  const dotColors = {
    brand: 'bg-purple-400',
    success: 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]',
    warning: 'bg-amber-400',
    danger: 'bg-rose-400',
    info: 'bg-sky-400',
    neutral: 'bg-gray-400',
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {pulse && (
        <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]} ${pulse ? 'animate-pulse' : ''}`} />
      )}
      <span>{children}</span>
    </span>
  );
};
