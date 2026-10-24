import { FC } from 'react'

interface StatusBadgeProps {
  status: 'running' | 'stopped' | 'error' | 'warning' | 'idle'
  label?: string
  className?: string
}

const statusStyles: Record<string, string> = {
  running: 'badge-success',
  stopped: 'badge-info',
  error: 'badge-error',
  warning: 'badge-warning',
  idle: 'badge-info',
}

const statusLabels: Record<string, string> = {
  running: 'Running',
  stopped: 'Stopped',
  error: 'Error',
  warning: 'Warning',
  idle: 'Idle',
}

export const StatusBadge: FC<StatusBadgeProps> = ({
  status,
  label,
  className = '',
}) => {
  return (
    <span className={`badge ${statusStyles[status]} ${className}`}>
      {label || statusLabels[status]}
    </span>
  )
}

export const ConnectionStatus: FC<{ connected: boolean }> = ({ connected }) => {
  return (
    <StatusBadge
      status={connected ? 'running' : 'error'}
      label={connected ? 'Connected' : 'Disconnected'}
    />
  )
}

export const ModelStatus: FC<{ loaded: boolean; loading?: boolean }> = ({
  loaded,
  loading,
}) => {
  if (loading) {
    return <StatusBadge status="warning" label="Loading..." />
  }
  return <StatusBadge status={loaded ? 'running' : 'idle'} />
}
