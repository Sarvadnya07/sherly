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
    default: 'bg-card border border-border-subtle',
    surface: 'bg-surface border border-border-subtle',
    glass: 'bg-card/80 backdrop-blur-md border border-border-medium',
    interactive: 'bg-card border border-border-subtle hover:border-border-medium hover:bg-card-hover cursor-pointer',
  };

  const paddings = {
    none: 'p-0',
    sm: 'p-2.5',
    md: 'p-4',
    lg: 'p-6',
  };

  return (
    <div className={`${baseStyles} ${variants[variant]} ${paddings[padding]} ${className}`} {...props}>
      {children}
    </div>
  );
};
