# Copyright 2018-2019 QuantumBlack Visual Analytics Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# NONINFRINGEMENT. IN NO EVENT WILL THE LICENSOR OR OTHER CONTRIBUTORS
# BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF, OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The QuantumBlack Visual Analytics Limited (“QuantumBlack”) name and logo
# (either separately or in combination, “QuantumBlack Trademarks”) are
# trademarks of QuantumBlack. The License does not grant you any right or
# license to the QuantumBlack Trademarks. You may not use the QuantumBlack
# Trademarks or any confusingly similar mark as a trademark for your product,
#     or use the QuantumBlack Trademarks in any other manner that might cause
# confusion in the marketplace, including but not limited to in advertising,
# on websites, or on software.
#
# See the License for the specific language governing permissions and
# limitations under the License.

"""``ParquetLocalDataSet`` is a data set used to load and save
data to local parquet files. It uses the ``pyarrow`` implementation,
which allows for multiple parts, compression, column selection etc.

Documentation on the PyArrow library features, compatibility
list and known caveats can also be found on their official guide at:

https://arrow.apache.org/docs/python/index.html
"""

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from kedro.io.core import (
    AbstractDataSet,
    DataSetError,
    ExistsMixin,
    FilepathVersionMixIn,
    Version,
)


class ParquetLocalDataSet(AbstractDataSet, ExistsMixin, FilepathVersionMixIn):
    """``AbstractDataSet`` with functionality for handling local parquet files.

    Example:
    ::

        >>> from kedro.io import ParquetLocalDataSet
        >>> import pandas as pd
        >>>
        >>> data = pd.DataFrame({'col1': [1, 2], 'col2': [4, 5],
        >>>                      'col3': [5, 6]})
        >>> data_set = ParquetLocalDataSet('myFile')
        >>> data_set.save(data)
        >>> loaded_data = data_set.load()
        >>> assert data.equals(loaded_data)
    """

    def _describe(self) -> Dict[str, Any]:
        return dict(
            filepath=self._filepath,
            engine=self._engine,
            load_args=self._load_args,
            save_args=self._save_args,
            version=self._version,
        )

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        filepath: str,
        engine: str = "auto",
        load_args: Dict[str, Any] = None,
        save_args: Dict[str, Any] = None,
        version: Version = None,
    ) -> None:
        """Creates a new instance of ``ParquetLocalDataSet`` pointing to a
        concrete filepath.

        Args:
            filepath: Path to a parquet file or a metadata file of a multipart
                parquet collection or the directory of a multipart parquet.

            engine: The engine to use, one of: `auto`, `fastparquet`,
                `pyarrow`. If `auto`, then the default behavior is to try
                `pyarrow`, falling back to `fastparquet` if `pyarrow` is
                unavailable.

            load_args: Additional loading options `pyarrow`:
                https://arrow.apache.org/docs/python/generated/pyarrow.parquet.read_table.html
                or `fastparquet`:
                https://fastparquet.readthedocs.io/en/latest/api.html#fastparquet.ParquetFile.to_pandas

            save_args: Additional saving options for `pyarrow`:
                https://arrow.apache.org/docs/python/generated/pyarrow.Table.html#pyarrow.Table.from_pandas
                or `fastparquet`:
                https://fastparquet.readthedocs.io/en/latest/api.html#fastparquet.write

            version: If specified, should be an instance of
                ``kedro.io.core.Version``. If its ``load`` attribute is
                None, the latest version will be loaded. If its ``save``
                attribute is None, save version will be autogenerated.

        """
        default_save_args = {"compression": None}
        default_load_args = {}

        self._filepath = filepath
        self._engine = engine

        self._load_args = (
            {**default_load_args, **load_args}
            if load_args is not None
            else default_load_args
        )
        self._save_args = (
            {**default_save_args, **save_args}
            if save_args is not None
            else default_save_args
        )
        self._version = version

    def _load(self) -> pd.DataFrame:
        load_path = self._get_load_path(self._filepath, self._version)
        return pd.read_parquet(load_path, engine=self._engine, **self._load_args)

    def _save(self, data: pd.DataFrame) -> None:
        save_path = Path(self._get_save_path(self._filepath, self._version))
        save_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_parquet(save_path, engine=self._engine, **self._save_args)

        load_path = Path(self._get_load_path(self._filepath, self._version))
        self._check_paths_consistency(
            str(load_path.absolute()), str(save_path.absolute())
        )

    def _exists(self) -> bool:
        try:
            path = self._get_load_path(self._filepath, self._version)
        except DataSetError:
            return False
        return Path(path).is_file()