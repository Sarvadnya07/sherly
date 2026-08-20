import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition duration-150 select-none rounded-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:opacity-40 disabled:pointer-events-none active:scale-[0.98] cursor-pointer';

  const variants = {
    primary: 'bg-brand hover:bg-brand-hover text-white shadow-subtle',
    secondary: 'bg-brand-surface hover:bg-brand/20 text-purple-300 border border-brand-border',
    ghost: 'bg-transparent hover:bg-white/[0.06] text-gray-300 hover:text-white',
    danger: 'bg-status-danger/15 hover:bg-status-danger/25 text-rose-400 border border-status-danger/30',
    outline: 'bg-transparent hover:bg-white/[0.04] text-gray-200 border border-white/[0.12]',
  };

  const sizes = {
    sm: 'text-[11px] px-2.5 py-1 gap-1.5 h-7',
    md: 'text-xs px-3 py-1.5 gap-2 h-8',
    lg: 'text-sm px-4 py-2 gap-2.5 h-10',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        icon && <span className="shrink-0">{icon}</span>
      )}
      {children && <span>{children}</span>}
    </button>
  );
};

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  'aria-label': string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'ghost' | 'secondary' | 'danger';
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  size = 'md',
  variant = 'ghost',
  className = '',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-md transition duration-150 select-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:opacity-40 disabled:pointer-events-none active:scale-[0.96] cursor-pointer';

  const variants = {
    ghost: 'text-gray-400 hover:text-gray-100 hover:bg-white/[0.08]',
    secondary: 'bg-white/[0.04] hover:bg-white/[0.08] text-gray-300 border border-white/[0.08]',
    danger: 'text-gray-400 hover:text-rose-400 hover:bg-rose-500/20',
  };

  const sizes = {
    sm: 'w-6 h-6 p-1 text-xs',
    md: 'w-7 h-7 p-1.5 text-xs',
    lg: 'w-8 h-8 p-2 text-sm',
  };

  return (
    <button
      type="button"
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {icon}
    </button>
  );
};
