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
    brand: 'bg-brand/10 text-txt-primary border border-brand/30',
    success: 'bg-status-success/10 text-status-success border border-status-success/20',
    warning: 'bg-status-warning/10 text-status-warning border border-status-warning/20',
    danger: 'bg-status-danger/10 text-status-danger border border-status-danger/20',
    info: 'bg-status-info/10 text-status-info border border-status-info/20',
    neutral: 'bg-card text-txt-secondary border border-border-subtle',
  };

  const sizes = {
    sm: 'text-[10px] px-1.5 py-0.5 leading-none',
    md: 'text-[11px] px-2 py-0.5 leading-tight',
  };

  const dotColors = {
    brand: 'bg-brand',
    success: 'bg-status-success shadow-[0_0_5px_rgba(16,185,129,0.7)]',
    warning: 'bg-status-warning',
    danger: 'bg-status-danger',
    info: 'bg-status-info',
    neutral: 'bg-txt-muted',
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {pulse && (
        <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]} animate-pulse shrink-0`} />
      )}
      <span>{children}</span>
    </span>
  );
};
