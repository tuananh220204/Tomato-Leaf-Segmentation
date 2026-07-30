// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SmartFarm {
    // Cấu trúc lưu trữ dấu vân tay dự báo
    struct Record {
        string recordHash;
        string modelName;
        uint256 timestamp;
    }

    // Mảng lưu trữ tất cả các bản ghi
    Record[] public records;

    // Sự kiện phát ra khi nạp thành công 1 bản ghi
    event RecordPegged(string recordHash, uint256 timestamp);

    // Hàm chốt dữ liệu lên Blockchain
    function pegRecord(string memory _hash, string memory _model) public {
        records.push(Record({
            recordHash: _hash,
            modelName: _model,
            timestamp: block.timestamp
        }));
        
        // Phát sự kiện để hệ thống web socket bên ngoài lăng nghe
        emit RecordPegged(_hash, block.timestamp);
    }

    // Hàm đọc tổng số lượng bản ghi
    function getTotalRecords() public view returns (uint256) {
        return records.length;
    }

    // Hàm lấy lại chi tiết một bản ghi bằng index
    function getRecord(uint256 _index) public view returns (string memory, string memory, uint256) {
        require(_index < records.length, "Record does not exist");
        Record memory rec = records[_index];
        return (rec.recordHash, rec.modelName, rec.timestamp);
    }
}