import React from 'react'

interface AvatarProps {
  src?: string
  alt?: string
  name?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const Avatar: React.FC<AvatarProps> = ({
  src,
  alt,
  name,
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  if (src) {
    return (
      <img
        src={src}
        alt={alt || name || 'Avatar'}
        className={`rounded-full ${sizeClasses[size]} ${className}`}
      />
    )
  }

  if (name) {
    return (
      <div
        className={`rounded-full ${sizeClasses[size]} bg-primary-600 text-white flex items-center justify-center font-medium ${className}`}
      >
        {getInitials(name)}
      </div>
    )
  }

  return (
    <div
      className={`rounded-full ${sizeClasses[size]} bg-gray-300 dark:bg-gray-600 ${className}`}
    />
  )
}

export default Avatar





