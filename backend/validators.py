class ConfigValidator:
    @staticmethod
    def validate_aws_config(config: dict) -> tuple[bool, str]:
        required_fields = {
            'bucket_name': str,
            'region': str
        }
        
        for field, field_type in required_fields.items():
            if field not in config:
                return False, f"Missing required field: {field}"
            if not isinstance(config[field], field_type):
                return False, f"Invalid type for {field}"
        
        return True, "" 