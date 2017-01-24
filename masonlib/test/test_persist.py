# COPYRIGHT MASONAMERICA
import os
import unittest

from masonlib.internal.persist import Persist


class PersistTest(unittest.TestCase):
    ID_TOKEN = 'akdfPODIFsplerHSPODif123'
    ACCESS_TOKEN = 'DSPFOSURELjopISUFpsd8USFDoiu34'

    def setUp(self):
        self.persist = Persist('.testmasonrc')
        self._write_test_tokens()
        self.persist.reload()

    def tearDown(self):
        os.remove(self.persist.file)

    def _write_test_tokens(self):
        test_data = {'id_token': self.ID_TOKEN,
                     'access_token': self.ACCESS_TOKEN}
        self.persist.write_tokens(test_data)

    def test_retrieve_id_token(self):
        assert(self.ID_TOKEN == self.persist.retrieve_id_token())

    def test_retrieve_access_token(self):
        assert(self.ACCESS_TOKEN == self.persist.retrieve_access_token())

    def test_write_tokens(self):
        secondary_id_token = 'DSPFOiudapofsd8uaesrljn'
        secondary_access_token = 'PSDOFislarkewpfdsauaser'
        secondary_data = {'id_token': secondary_id_token,
                     'access_token': secondary_access_token}
        self.persist.write_tokens(secondary_data)

        # reload
        self.persist.reload()
        assert(secondary_id_token == self.persist.retrieve_id_token())
        assert(secondary_access_token == self.persist.retrieve_access_token())

if __name__ == '__main__':
    unittest.main()