import { useConfig } from '../contexts/ConfigContext'
import { CredentialsForm } from '../components/aws/CredentialsForm'
import { BucketSelector } from '../components/aws/BucketSelector'

export function Settings() {
  const { config } = useConfig()

  return (
    <div>
      <h1>Settings</h1>
      <div>
        <h2>AWS Configuration</h2>
        <CredentialsForm />
        {config.aws_access_key_id && <BucketSelector />}
      </div>
    </div>
  )
}
