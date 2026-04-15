

from rest_framework import serializers
from .models import ScanHistory,SUBJECT_CHOICES, AiPersonalization


class ScanRequestSerializer(serializers.Serializer):
    """Validates incoming scan request before AI call."""
    subject = serializers.ChoiceField(choices=[c[0] for c in SUBJECT_CHOICES])#❓❓❓why choicefield used, isn't choice field , method field used when the field isn't present in model?
    image = serializers.ImageField()#❓❓❓ why I mentioned image separately here evenif its included on the model?
    question = serializers.CharField(required=False, allow_blank=True, max_length=500)
 
#❓❓❓why some serializers contain class Meta some not

class ScanHistorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ScanHistory
        fields = ['id','subject','image_url','question','ai_response']

    def get_image_url(self, obj):
        request = self.context.get('request')#❓❓❓ what does this line means, what does obj contain,all the scanhistory model field?
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class AiPersonalizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiPersonalization
        fields = ['model', 'response_sytel', 'dificulty_level', 'language', 'subject_focus_area']
















