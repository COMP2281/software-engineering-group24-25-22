from rest_framework import serializers

class DocumentSerializer(serializers.Serializer):
    """Base serializer for MongoEngine documents"""
    
    def create(self, validated_data):
        """Create a new instance from validated data"""
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        """Update an existing instance with validated data"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
