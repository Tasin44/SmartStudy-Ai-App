# core/pagination.py
# Reusable pagination class used across all list endpoints
 
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
 
 
class StandardPagination(PageNumberPagination):
    """
    Default paginator: 20 items/page, client can override up to 100.
    Always paginate list endpoints — never return unbounded querysets.
    """
    page_size = 20                    # default page size
    page_size_query_param = 'page_size'  # ?page_size=50
    max_page_size = 100               # hard cap to prevent abuse
 
    def get_paginated_response(self, data):
        # Wraps paginated data in our standard envelope
        return Response({
            "success": True,
            "statusCode": 200,
            "message": "Data fetched successfully.",
            "data": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data
            }
        })