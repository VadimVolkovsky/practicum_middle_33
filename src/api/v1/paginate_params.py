from functools import lru_cache
from typing import Annotated
from fastapi import Query


class PaginatedParams:
    def __init__(self, page_size, page_number):
        self.page_size = page_size
        self.page_number = page_number

    def get_page_size(self):
        return self.page_size

    def get_page_number(self):
        return self.page_number


@lru_cache()
def get_paginated_params(
        page_size: Annotated[int, Query(description='Pagination page size', ge=1)] = 100,
        page_number: Annotated[int, Query(description='Pagination page number', ge=1)] = 1,
) -> PaginatedParams:
    return PaginatedParams(page_size, page_number)
