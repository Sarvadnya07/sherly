import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'surface' | 'glass' | 'interactive';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'md',
  className = '',
  ...props
}) => {
  const baseStyles = 'rounded-lg transition duration-150';

  const variants = {
    default: 'bg-card border border-white/[0.06]',
    surface: 'bg-surface border border-white/[0.04]',
    glass: 'bg-canvas/80 backdrop-blur-md border border-white/[0.08]',
    interactive: 'bg-card border border-white/[0.06] hover:border-brand-border hover:bg-card-hover cursor-pointer',
  };

  const paddings = {
    none: 'p-0',
    sm: 'p-2.5',
    md: 'p-3.5',
    lg: 'p-5',
  };

  return (
    <div className={`${baseStyles} ${variants[variant]} ${paddings[padding]} ${className}`} {...props}>
      {children}
    </div>
  );
};
